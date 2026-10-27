import os
import sys
import time
import asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from server import app

async def run_integration_tests():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Network info
        res = await client.get("/api/network-info")
        assert res.status_code == 200
        data = res.json()
        assert "ip" in data
        assert "qr_code" in data
        assert data["qr_code"].startswith("data:image/png;base64,")
        print("✓ Network info and QR code endpoint passed")

        # 2. Voices list
        res = await client.get("/api/voices")
        assert res.status_code == 200
        vdata = res.json()
        assert len(vdata["kokoro_voices"]) > 10
        print("✓ Voices catalogue endpoint passed")

        # 3. Upload mini book
        book_content = (
            "# Chapter 1: The Quick Spark\n\n"
            "The quick brown fox jumps over the lazy dog."
        )
        files = {"file": ("integration_book.txt", book_content.encode("utf-8"), "text/plain")}
        res = await client.post("/api/upload", files=files)
        assert res.status_code == 200
        book_data = res.json()
        book_id = book_data["book_id"]
        assert len(book_data["chapters"]) >= 1
        print(f"✓ Book uploaded and parsed: '{book_data['title']}'")

        # 4. Start compile with Kokoro GPU
        compile_payload = {
            "book_id": book_id,
            "voice": "af_heart",
            "engine": "kokoro",
            "speed": "1.0",
            "output_format": "m4b"
        }
        res = await client.post("/api/compile", data=compile_payload)
        assert res.status_code == 200
        job_info = res.json()
        job_id = job_info["job_id"]
        print(f"✓ Compilation job created: {job_id}")

        # 5. Async poll for completion
        completed = False
        output_file = None
        for _ in range(60):
            await asyncio.sleep(1.0)
            res = await client.get(f"/api/jobs/{job_id}")
            assert res.status_code == 200
            st = res.json()
            print(f"  [Progress] {st['status']} - {st['progress']}% - {st['current_chapter_title']}")
            if st["status"] == "completed":
                completed = True
                output_file = st["output_file"]
                break
            elif st["status"] in ["failed", "cancelled"]:
                raise RuntimeError(f"Job ended unexpectedly: {st['status']} - {st.get('error_message')}")

        assert completed, "Compilation job did not complete in time"
        print(f"✓ Compilation completed successfully! Output: {output_file}")

        # 6. Check library
        res = await client.get("/api/audiobooks")
        assert res.status_code == 200
        audiobooks = res.json()
        assert any(ab["filename"] == output_file for ab in audiobooks)
        print("✓ Library listed compiled audiobook")

        # 7. Check download
        res = await client.get(f"/api/download/{output_file}")
        assert res.status_code == 200
        assert len(res.content) > 1000
        print("✓ Download endpoint served audiobook bytes")

        # 8. Clean up
        res = await client.delete(f"/api/audiobooks/{output_file}")
        assert res.status_code == 200
        print("✓ Cleanup delete endpoint passed")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
    print("\n🎉 ALL ASYNC INTEGRATION TESTS PASSED PERFECTLY!")
