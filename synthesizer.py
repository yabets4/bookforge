import os
import time
import asyncio
import uuid
import re
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import soundfile as sf
import numpy as np

import json
from kokoro_engine import kokoro_engine
from packager import packager, get_audio_duration_seconds


def transcript_path(audio_file: str) -> str:
    """Book.m4b → Book.m4b.words.json (read-along text with word times)."""
    return audio_file + ".words.json"


def group_words(words: List[list], target: int = 45) -> List[List[list]]:
    """Cut a long run of words into passages, ending each at a sentence end once it has ~target words."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= target and w[0].rstrip().endswith((".", "!", "?", "”", '"')):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out

def chunk_text_by_sentences(text: str, max_chars: int = 500) -> List[str]:
    """Split long text into natural sentence batches for safe, reliable synthesis."""
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    raw_sentences = sentence_endings.split(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for s in raw_sentences:
        s = s.strip()
        if not s:
            continue
        if current_length + len(s) > max_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [s]
            current_length = len(s)
        else:
            current_chunk.append(s)
            current_length += len(s)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text]

class CompilationJob:
    def __init__(
        self,
        job_id: str,
        book: Dict[str, Any],
        voice: str = "af_heart",
        engine: str = "kokoro",
        speed: float = 1.0,
        output_format: str = "m4b",
        selected_chapter_ids: Optional[List[int]] = None
    ):
        self.job_id = job_id
        self.book = book
        self.voice = voice
        self.engine = engine
        self.speed = speed
        self.output_format = output_format.lower()
        self.selected_chapter_ids = selected_chapter_ids

        self.status = "queued" # queued, running, packaging, completed, failed, cancelled
        self.progress = 0.0
        self.current_chapter_title = ""
        self.current_chapter_index = 0
        self.total_chapters = 0
        self.start_time = 0.0
        self.elapsed_seconds = 0.0
        self.eta_seconds = 0.0
        self.error_message: Optional[str] = None
        self.output_file: Optional[str] = None
        self.output_size_bytes = 0
        self.logs: List[str] = []
        self._cancel_requested = False
        self._subscribers: List[asyncio.Queue] = []

    def log(self, message: str):
        entry = f"[{time.strftime('%H:%M:%S')}] {message}"
        self.logs.append(entry)
        if len(self.logs) > 200:
            self.logs.pop(0)
        print(f"[{self.job_id}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "book_id": self.book.get("book_id"),
            "book_title": self.book.get("title"),
            "book_author": self.book.get("author"),
            "voice": self.voice,
            "engine": self.engine,
            "speed": self.speed,
            "output_format": self.output_format,
            "status": self.status,
            "progress": round(self.progress, 1),
            "current_chapter_title": self.current_chapter_title,
            "current_chapter_index": self.current_chapter_index,
            "total_chapters": self.total_chapters,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "eta_seconds": round(self.eta_seconds, 1),
            "error_message": self.error_message,
            "output_file": os.path.basename(self.output_file) if self.output_file else None,
            "output_size_bytes": self.output_size_bytes,
            "recent_logs": self.logs[-5:]
        }

    def cancel(self):
        self._cancel_requested = True
        self.status = "cancelled"
        self.log("Job cancellation requested.")

class SynthesisManager:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        self.jobs: Dict[str, CompilationJob] = {}
        self._active_tasks: Dict[str, asyncio.Task] = {}

    def get_job(self, job_id: str) -> Optional[CompilationJob]:
        return self.jobs.get(job_id)

    def create_job(
        self,
        book: Dict[str, Any],
        voice: str = "af_heart",
        engine: str = "kokoro",
        speed: float = 1.0,
        output_format: str = "m4b",
        selected_chapter_ids: Optional[List[int]] = None
    ) -> CompilationJob:
        job_id = str(uuid.uuid4())[:8]
        job = CompilationJob(
            job_id=job_id,
            book=book,
            voice=voice,
            engine=engine,
            speed=speed,
            output_format=output_format,
            selected_chapter_ids=selected_chapter_ids
        )
        self.jobs[job_id] = job
        return job

    def start_job(self, job_id: str):
        job = self.jobs.get(job_id)
        if not job or job.status == "running":
            return
        task = asyncio.create_task(self._run_job(job))
        self._active_tasks[job_id] = task

    async def _run_job(self, job: CompilationJob):
        job.status = "running"
        job.start_time = time.time()
        job.log(f"Starting compilation for '{job.book['title']}' using engine: {job.engine}, voice: {job.voice}")

        temp_dir = os.path.join(self.storage_dir, "temp", job.job_id)
        output_dir = os.path.join(self.storage_dir, "output")
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 1. Filter chapters
            all_chapters = job.book.get("chapters", [])
            if job.selected_chapter_ids:
                chapters_to_process = [c for c in all_chapters if c["id"] in job.selected_chapter_ids]
            else:
                chapters_to_process = [c for c in all_chapters if c.get("selected", True)]

            if not chapters_to_process:
                raise ValueError("No chapters selected for synthesis.")

            job.total_chapters = len(chapters_to_process)
            total_chars = sum(c["char_count"] for c in chapters_to_process)
            processed_chars = 0

            chapter_audio_files = []
            # read-along text: passages of [word, start, end], seconds from the start of the book
            paras: List[List[list]] = []
            chapters_meta: List[Dict[str, Any]] = []
            book_sec = 0.0

            # 2. Synthesize each chapter
            for idx, chap in enumerate(chapters_to_process, start=1):
                if job._cancel_requested:
                    job.log("Compilation cancelled by user.")
                    job.status = "cancelled"
                    return

                job.current_chapter_index = idx
                job.current_chapter_title = chap["title"]
                job.log(f"Synthesizing [{idx}/{job.total_chapters}]: {chap['title']} ({chap['word_count']} words)")

                chap_audio_path = os.path.join(temp_dir, f"chap_{idx:03d}.wav")
                chap_text = chap["text"]
                chap_first_para = len(paras)

                if job.engine == "kokoro":
                    # Chunk long chapter text to update progress smoothly
                    chunks = chunk_text_by_sentences(chap_text, max_chars=400)
                    audio_arrays = []
                    chap_sec = 0.0

                    for c_idx, chunk in enumerate(chunks):
                        if job._cancel_requested:
                            job.status = "cancelled"
                            return

                        audio_arr, words = await kokoro_engine.synthesize_text_timed(chunk, voice=job.voice, speed=job.speed)
                        if len(audio_arr) > 0:
                            audio_arrays.append(audio_arr)
                            # one passage per chunk, word times relative to the whole book
                            at = book_sec + chap_sec
                            paras.append([[w, round(at + s, 3), round(at + e, 3)] for w, s, e in words])
                            chap_sec += len(audio_arr) / kokoro_engine.sample_rate

                        processed_chars += len(chunk)
                        # Progress & ETA calculation
                        job.progress = min(98.0, (processed_chars / max(1, total_chars)) * 95.0)
                        job.elapsed_seconds = time.time() - job.start_time
                        if job.progress > 2.0:
                            total_estimated_sec = (job.elapsed_seconds / (job.progress / 100.0))
                            job.eta_seconds = max(0.0, total_estimated_sec - job.elapsed_seconds)

                    # Combine all sentence audio chunks for this chapter
                    if audio_arrays:
                        full_chap_audio = np.concatenate(audio_arrays)
                    else:
                        full_chap_audio = np.zeros(24000, dtype=np.float32)

                    sf.write(chap_audio_path, full_chap_audio, kokoro_engine.sample_rate)

                else:
                    # Edge-TTS alternative
                    import edge_tts
                    edge_voice = job.voice if "Neural" in job.voice else "en-US-ChristopherNeural"
                    rate_pct = int((job.speed - 1.0) * 100)
                    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

                    communicate = edge_tts.Communicate(chap_text, edge_voice, rate=rate_str, boundary="WordBoundary")
                    edge_words = []
                    with open(chap_audio_path, "wb") as audio_f:
                        async for msg in communicate.stream():
                            if msg["type"] == "audio":
                                audio_f.write(msg["data"])
                            elif msg["type"] == "WordBoundary":   # offsets in 100 ns units
                                s = msg["offset"] / 1e7
                                edge_words.append([msg["text"] + " ", round(book_sec + s, 3), round(book_sec + s + msg["duration"] / 1e7, 3)])
                    paras.extend(group_words(edge_words))
                    processed_chars += chap["char_count"]
                    job.progress = min(98.0, (processed_chars / max(1, total_chars)) * 95.0)
                    job.elapsed_seconds = time.time() - job.start_time
                    if job.progress > 2.0:
                        total_estimated_sec = (job.elapsed_seconds / (job.progress / 100.0))
                        job.eta_seconds = max(0.0, total_estimated_sec - job.elapsed_seconds)

                chapter_audio_files.append({
                    "title": chap["title"],
                    "audio_path": chap_audio_path
                })
                chapters_meta.append({"title": chap["title"], "start": round(book_sec, 3), "para": chap_first_para})
                book_sec += get_audio_duration_seconds(chap_audio_path)

            # 3. Packaging
            job.status = "packaging"
            job.progress = 96.0
            job.log(f"Packaging {len(chapter_audio_files)} chapters into {job.output_format.upper()}...")

            safe_book_title = "".join(c for c in job.book["title"] if c.isalnum() or c in " -_").strip() or "Audiobook"
            cover_img = job.book.get("cover_path")

            if job.output_format == "m4b":
                out_path = os.path.join(output_dir, f"{safe_book_title}.m4b")
                # Ensure unique filename if already exists
                if os.path.exists(out_path):
                    out_path = os.path.join(output_dir, f"{safe_book_title}_{job.job_id}.m4b")

                final_file = await asyncio.get_running_loop().run_in_executor(
                    None,
                    packager.build_m4b,
                    chapter_audio_files,
                    out_path,
                    job.book["title"],
                    job.book["author"],
                    cover_img
                )
            else:
                out_path = os.path.join(output_dir, f"{safe_book_title}.zip")
                if os.path.exists(out_path):
                    out_path = os.path.join(output_dir, f"{safe_book_title}_{job.job_id}.zip")

                final_file = await asyncio.get_running_loop().run_in_executor(
                    None,
                    packager.build_mp3_zip,
                    chapter_audio_files,
                    out_path,
                    job.book["title"],
                    job.book["author"],
                    cover_img
                )

            job.output_file = final_file
            job.output_size_bytes = os.path.getsize(final_file)
            if paras:
                with open(transcript_path(final_file), "w", encoding="utf-8") as tf:
                    json.dump({"version": 1, "chapters": chapters_meta, "paras": paras}, tf, ensure_ascii=False, separators=(",", ":"))
            job.progress = 100.0
            job.eta_seconds = 0.0
            job.elapsed_seconds = time.time() - job.start_time
            job.status = "completed"
            job.log(f"Successfully compiled audiobook: {os.path.basename(final_file)} ({job.output_size_bytes / (1024*1024):.1f} MB)")

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.log(f"Error during compilation: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self._active_tasks.pop(job.job_id, None)
            # Clean up temp wav files
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

# Global manager instance initialized in server.py
