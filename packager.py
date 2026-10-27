import os
import subprocess
import zipfile
import shutil
from typing import List, Dict, Optional, Any
from pathlib import Path
import imageio_ffmpeg
import mutagen
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, APIC

def get_audio_duration_seconds(file_path: str) -> float:
    """Read audio duration using mutagen."""
    audio = mutagen.File(file_path)
    if audio and audio.info and hasattr(audio.info, "length"):
        return float(audio.info.length)
    
    # Fallback to ffprobe if mutagen length is not available
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffprobe_cmd = [
        ffmpeg_exe, "-i", file_path, "-hide_banner"
    ]
    res = subprocess.run(ffprobe_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", res.stderr)
    if m:
        h, mn, s = float(m.group(1)), float(m.group(2)), float(m.group(3))
        return h * 3600 + mn * 60 + s
    return 0.0

class AudiobookPackager:
    def __init__(self):
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def build_m4b(
        self,
        chapter_files: List[Dict[str, Any]], # [{"title": "Chapter 1", "audio_path": "/path/to/wav"}]
        output_file: str,
        title: str,
        author: str,
        cover_image: Optional[str] = None
    ) -> str:
        """Concatenate chapter audio files into an M4B audiobook with chapter marks and cover art."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        temp_dir = os.path.join(os.path.dirname(output_file), "m4b_build_temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # 1. Create concat list and calculate chapter offsets
            concat_list_file = os.path.join(temp_dir, "concat.txt")
            metadata_file = os.path.join(temp_dir, "metadata.txt")

            current_ms = 0
            metadata_lines = [
                ";FFMETADATA1",
                f"title={title}",
                f"artist={author}",
                f"album={title}",
                "genre=Audiobook",
                ""
            ]

            with open(concat_list_file, "w", encoding="utf-8") as concat_f:
                for chap in chapter_files:
                    audio_path = chap["audio_path"]
                    # Escape path for FFmpeg concat demuxer
                    safe_path = audio_path.replace("\\", "/").replace("'", "'\\''")
                    concat_f.write(f"file '{safe_path}'\n")

                    duration_sec = get_audio_duration_seconds(audio_path)
                    duration_ms = int(duration_sec * 1000)
                    end_ms = current_ms + duration_ms

                    metadata_lines.extend([
                        "[CHAPTER]",
                        "TIMEBASE=1/1000",
                        f"START={current_ms}",
                        f"END={end_ms}",
                        f"title={chap['title']}",
                        ""
                    ])
                    current_ms = end_ms

            with open(metadata_file, "w", encoding="utf-8") as meta_f:
                meta_f.write("\n".join(metadata_lines))

            # 2. Run FFmpeg to concatenate, encode to AAC (M4B), and inject chapter metadata
            # Base command
            cmd = [
                self.ffmpeg_exe, "-y",
                "-f", "concat", "-safe", "0", "-i", concat_list_file,
                "-i", metadata_file,
                "-map_metadata", "1"
            ]

            # Cover art mapping if present
            if cover_image and os.path.exists(cover_image):
                cmd.extend([
                    "-i", cover_image,
                    "-map", "0:a",
                    "-map", "2:v",
                    "-disposition:v:0", "attached_pic"
                ])
            else:
                cmd.extend(["-map", "0:a"])

            cmd.extend([
                "-c:a", "aac",
                "-b:a", "64k",
                "-movflags", "+faststart",
                output_file
            ])

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                print(f"[AudiobookPackager] FFmpeg warning/error: {res.stderr[-500:]}")
                # Fallback to copy codec or single stream if cover failed
                cmd_fallback = [
                    self.ffmpeg_exe, "-y",
                    "-f", "concat", "-safe", "0", "-i", concat_list_file,
                    "-i", metadata_file,
                    "-map_metadata", "1",
                    "-map", "0:a",
                    "-c:a", "aac",
                    "-b:a", "64k",
                    "-movflags", "+faststart",
                    output_file
                ]
                subprocess.run(cmd_fallback, check=True)

            # 3. Apply MP4 metadata tags via mutagen
            try:
                mp4 = MP4(output_file)
                mp4["\xa9nam"] = title
                mp4["\xa9ART"] = author
                mp4["\xa9alb"] = title
                mp4["\xa9gen"] = "Audiobook"
                if cover_image and os.path.exists(cover_image):
                    with open(cover_image, "rb") as cf:
                        cov_data = cf.read()
                    image_format = MP4Cover.FORMAT_PNG if cover_image.lower().endswith(".png") else MP4Cover.FORMAT_JPEG
                    mp4["covr"] = [MP4Cover(cov_data, imageformat=image_format)]
                mp4.save()
            except Exception as e:
                print(f"[AudiobookPackager] Note on mutagen MP4 tag write: {e}")

            return output_file

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def build_mp3_zip(
        self,
        chapter_files: List[Dict[str, Any]],
        output_zip: str,
        title: str,
        author: str,
        cover_image: Optional[str] = None
    ) -> str:
        """Package chapters as a tagged MP3 ZIP archive."""
        os.makedirs(os.path.dirname(output_zip), exist_ok=True)
        temp_dir = os.path.join(os.path.dirname(output_zip), "zip_build_temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            mp3_paths = []
            total = len(chapter_files)

            for idx, chap in enumerate(chapter_files, start=1):
                clean_chap_title = "".join(c for c in chap['title'] if c.isalnum() or c in " -_").strip()
                mp3_name = f"{idx:02d} - {clean_chap_title or f'Chapter {idx}'}.mp3"
                mp3_path = os.path.join(temp_dir, mp3_name)

                # Convert source audio to MP3
                cmd = [
                    self.ffmpeg_exe, "-y",
                    "-i", chap["audio_path"],
                    "-codec:a", "libmp3lame",
                    "-q:a", "4",
                    mp3_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                # Tag MP3 with ID3
                try:
                    audio = ID3()
                    audio.add(TIT2(encoding=3, text=chap['title']))
                    audio.add(TPE1(encoding=3, text=author))
                    audio.add(TALB(encoding=3, text=title))
                    audio.add(TRCK(encoding=3, text=f"{idx}/{total}"))

                    if cover_image and os.path.exists(cover_image):
                        mime = "image/png" if cover_image.lower().endswith(".png") else "image/jpeg"
                        with open(cover_image, "rb") as cf:
                            audio.add(APIC(
                                encoding=3,
                                mime=mime,
                                type=3,
                                desc="Cover",
                                data=cf.read()
                            ))
                    audio.save(mp3_path)
                except Exception as e:
                    print(f"[AudiobookPackager] Tagging MP3 error: {e}")

                mp3_paths.append((mp3_path, mp3_name))

            # Create ZIP
            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zip_f:
                for file_path, arcname in mp3_paths:
                    zip_f.write(file_path, arcname)

            return output_zip

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

# Global singleton
packager = AudiobookPackager()
