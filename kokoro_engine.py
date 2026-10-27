import os
import torch
import numpy as np
import soundfile as sf
from typing import Dict, List, Optional, Tuple
import asyncio
import threading
from pathlib import Path

# Voice catalog with metadata
KOKORO_VOICES = [
    # American Female
    {"id": "af_heart", "name": "Heart", "gender": "Female", "accent": "American", "desc": "Warm, emotional & expressive (Flagship)"},
    {"id": "af_bella", "name": "Bella", "gender": "Female", "accent": "American", "desc": "Clear, friendly & natural tone"},
    {"id": "af_nicole", "name": "Nicole", "gender": "Female", "accent": "American", "desc": "Smooth, calm & composed"},
    {"id": "af_aoede", "name": "Aoede", "gender": "Female", "accent": "American", "desc": "Deep, rich & melodic"},
    {"id": "af_kore", "name": "Kore", "gender": "Female", "accent": "American", "desc": "Bright, engaging & articulate"},
    {"id": "af_sarah", "name": "Sarah", "gender": "Female", "accent": "American", "desc": "Professional & balanced"},
    {"id": "af_nova", "name": "Nova", "gender": "Female", "accent": "American", "desc": "Vibrant, modern & clear"},
    {"id": "af_sky", "name": "Sky", "gender": "Female", "accent": "American", "desc": "Light, warm & inviting"},
    {"id": "af_alloy", "name": "Alloy", "gender": "Female", "accent": "American", "desc": "Crisp & neutral"},
    {"id": "af_jessica", "name": "Jessica", "gender": "Female", "accent": "American", "desc": "Conversational & expressive"},
    {"id": "af_river", "name": "River", "gender": "Female", "accent": "American", "desc": "Relaxed & smooth"},
    
    # American Male
    {"id": "am_michael", "name": "Michael", "gender": "Male", "accent": "American", "desc": "Rich, deep audiobook narrator"},
    {"id": "am_adam", "name": "Adam", "gender": "Male", "accent": "American", "desc": "Confident, clear & steady"},
    {"id": "am_echo", "name": "Echo", "gender": "Male", "accent": "American", "desc": "Resonant & grounded"},
    {"id": "am_eric", "name": "Eric", "gender": "Male", "accent": "American", "desc": "Natural, conversational tone"},
    {"id": "am_liam", "name": "Liam", "gender": "Male", "accent": "American", "desc": "Articulate & engaging"},
    {"id": "am_onyx", "name": "Onyx", "gender": "Male", "accent": "American", "desc": "Deep, authoritative & commanding"},
    {"id": "am_puck", "name": "Puck", "gender": "Male", "accent": "American", "desc": "Energetic & youthful"},
    {"id": "am_fenrir", "name": "Fenrir", "gender": "Male", "accent": "American", "desc": "Powerful & dramatic"},

    # British Female
    {"id": "bf_alice", "name": "Alice", "gender": "Female", "accent": "British", "desc": "Refined, sophisticated narrator"},
    {"id": "bf_emma", "name": "Emma", "gender": "Female", "accent": "British", "desc": "Warm, classic British tone"},
    {"id": "bf_isabella", "name": "Isabella", "gender": "Female", "accent": "British", "desc": "Polished & elegant"},
    {"id": "bf_lily", "name": "Lily", "gender": "Female", "accent": "British", "desc": "Crisp, clear & delicate"},

    # British Male
    {"id": "bm_george", "name": "George", "gender": "Male", "accent": "British", "desc": "Classic literary storyteller"},
    {"id": "bm_fable", "name": "Fable", "gender": "Male", "accent": "British", "desc": "Distinctive, poetic & dramatic"},
    {"id": "bm_lewis", "name": "Lewis", "gender": "Male", "accent": "British", "desc": "Steady, documentary-style delivery"},
    {"id": "bm_daniel", "name": "Daniel", "gender": "Male", "accent": "British", "desc": "Deep, distinguished voice"}
]

class KokoroEngine:
    def __init__(self, device: Optional[str] = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[KokoroEngine] Target device: {self.device}")
        if self.device == "cuda":
            print(f"[KokoroEngine] GPU Name: {torch.cuda.get_device_name(0)}")
            
        self.sample_rate = 24000
        self._pipelines: Dict[str, any] = {}
        self._lock = asyncio.Lock()
        self._gpu = threading.Lock()   # one synthesis at a time: two jobs (or a job + a voice sample) on a 2 GB card run out of memory

    def get_pipeline(self, lang_code: str = 'a'):
        """Lazy load and cache KPipeline for language ('a' for US English, 'b' for UK English)."""
        if lang_code not in self._pipelines:
            from kokoro import KPipeline
            print(f"[KokoroEngine] Loading KPipeline (lang='{lang_code}', device='{self.device}')...")
            try:
                self._pipelines[lang_code] = KPipeline(lang_code=lang_code, device=self.device)
            except Exception as e:
                print(f"[KokoroEngine] Failed to load on {self.device}: {e}. Retrying on CPU...")
                self.device = "cpu"
                self._pipelines[lang_code] = KPipeline(lang_code=lang_code, device="cpu")
            print(f"[KokoroEngine] KPipeline ('{lang_code}') loaded successfully.")
        return self._pipelines[lang_code]

    def _determine_lang_code(self, voice_id: str) -> str:
        """Map voice prefix to language code: 'b' for British, 'a' for American."""
        if voice_id.startswith('b'):
            return 'b'
        return 'a'

    def synthesize_text_sync(self, text: str, voice: str = "af_heart", speed: float = 1.0) -> np.ndarray:
        """Synchronously synthesize text to numpy audio array."""
        text = text.strip()
        if not text:
            return np.zeros(0, dtype=np.float32)

        lang_code = self._determine_lang_code(voice)
        audio_pieces = []
        with self._gpu:
            pipeline = self.get_pipeline(lang_code)
            generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')
            for _, _, audio in generator:
                if audio is not None and len(audio) > 0:
                    audio_pieces.append(audio)

        if not audio_pieces:
            return np.zeros(0, dtype=np.float32)

        return np.concatenate(audio_pieces)

    def synthesize_text_timed_sync(self, text: str, voice: str = "af_heart", speed: float = 1.0):
        """Like synthesize_text_sync, plus when each word is spoken: [[word, start_sec, end_sec], ...].
        Punctuation sticks to the word before it, so the words read back as the original text."""
        text = text.strip()
        if not text:
            return np.zeros(0, dtype=np.float32), []

        lang_code = self._determine_lang_code(voice)
        audio_pieces, words = [], []
        offset = 0.0
        with self._gpu:
            pipeline = self.get_pipeline(lang_code)
            for result in pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+'):
                audio = result.audio
                if audio is None or len(audio) == 0:
                    continue
                for tok in (result.tokens or []):
                    if tok.start_ts is None or tok.end_ts is None:
                        continue
                    start, end = offset + tok.start_ts, offset + tok.end_ts
                    piece = tok.text + (tok.whitespace or "")
                    if words and not any(ch.isalnum() for ch in tok.text):
                        words[-1][0] += piece             # "friend" + "." → "friend."
                        words[-1][2] = end
                    elif words and not words[-1][0].endswith(" ") and not any(ch.isalnum() for ch in words[-1][0]):
                        words[-1][0] += piece             # opening quote / bracket joins the next word
                        words[-1][2] = end
                    else:
                        words.append([piece, start, end])
                audio_pieces.append(audio)
                offset += len(audio) / self.sample_rate

        if not audio_pieces:
            return np.zeros(0, dtype=np.float32), []
        return np.concatenate(audio_pieces), words

    async def synthesize_text_timed(self, text: str, voice: str = "af_heart", speed: float = 1.0):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.synthesize_text_timed_sync, text, voice, speed)

    async def synthesize_text(self, text: str, voice: str = "af_heart", speed: float = 1.0) -> np.ndarray:
        """Asynchronously synthesize text on background thread."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.synthesize_text_sync, text, voice, speed)

    async def synthesize_to_file(self, text: str, output_path: str, voice: str = "af_heart", speed: float = 1.0) -> float:
        """Synthesize text and write to WAV file. Returns audio duration in seconds."""
        audio = await self.synthesize_text(text, voice, speed)
        if len(audio) == 0:
            return 0.0

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        sf.write(output_path, audio, self.sample_rate)
        duration = len(audio) / self.sample_rate
        return duration

    async def get_or_create_voice_preview(self, voice_id: str, preview_dir: str) -> str:
        """Generate or retrieve a 3-second audio preview file for a voice."""
        os.makedirs(preview_dir, exist_ok=True)
        preview_file = os.path.join(preview_dir, f"{voice_id}.mp3")
        if os.path.exists(preview_file):
            return preview_file

        sample_text = f"Hello! I am {voice_id.split('_')[1].title()}. I will narrate your book with natural neural speech."
        temp_wav = os.path.join(preview_dir, f"{voice_id}_temp.wav")
        await self.synthesize_to_file(sample_text, temp_wav, voice=voice_id, speed=1.0)
        
        # Convert WAV to lightweight MP3 using imageio_ffmpeg
        import imageio_ffmpeg
        import subprocess
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [ffmpeg_exe, "-y", "-i", temp_wav, "-codec:a", "libmp3lame", "-b:a", "64k", preview_file]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
            
        return preview_file

# Global singleton
kokoro_engine = KokoroEngine()
