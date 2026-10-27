import os
import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
from mutagen.mp4 import MP4
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from packager import AudiobookPackager

def test_packager():
    with tempfile.TemporaryDirectory() as tmpdir:
        packager = AudiobookPackager()

        # Generate 2 dummy audio files (1.5 seconds each of 440Hz sine wave)
        sr = 24000
        t = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
        audio1 = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        audio2 = (0.3 * np.sin(2 * np.pi * 550 * t)).astype(np.float32)

        chap1_path = os.path.join(tmpdir, "chap1.wav")
        chap2_path = os.path.join(tmpdir, "chap2.wav")
        sf.write(chap1_path, audio1, sr)
        sf.write(chap2_path, audio2, sr)

        chapters = [
            {"title": "Chapter 1: The Sparks", "audio_path": chap1_path},
            {"title": "Chapter 2: The Flame", "audio_path": chap2_path}
        ]

        # 1. Test M4B packaging
        m4b_output = os.path.join(tmpdir, "output.m4b")
        out_m4b = packager.build_m4b(
            chapter_files=chapters,
            output_file=m4b_output,
            title="Fire Chronicles",
            author="Prometheus",
            cover_image=None
        )

        assert os.path.exists(out_m4b), "M4B file was not created"
        assert os.path.getsize(out_m4b) > 1000, "M4B file is suspiciously small"

        # Verify MP4 tags
        mp4 = MP4(out_m4b)
        tag_title = mp4.get("\xa9nam")
        tag_artist = mp4.get("\xa9ART")
        assert tag_title == ["Fire Chronicles"], f"Unexpected title tag: {tag_title}"
        assert tag_artist == ["Prometheus"], f"Unexpected artist tag: {tag_artist}"
        print("✓ M4B packaging and chapter embedding passed")

        # 2. Test MP3 ZIP packaging
        zip_output = os.path.join(tmpdir, "output.zip")
        out_zip = packager.build_mp3_zip(
            chapter_files=chapters,
            output_zip=zip_output,
            title="Fire Chronicles",
            author="Prometheus",
            cover_image=None
        )

        assert os.path.exists(out_zip), "ZIP file was not created"
        with zipfile.ZipFile(out_zip, 'r') as zf:
            names = zf.namelist()
            assert len(names) == 2, f"Expected 2 mp3 files in zip, got {names}"
        print("✓ MP3 ZIP packaging passed")

if __name__ == "__main__":
    test_packager()
    print("All packager tests successfully passed!")
