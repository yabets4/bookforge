import os
import io
import socket
import base64
import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException, Query
import time
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import qrcode
import qrcode.image.pil

from kokoro_engine import kokoro_engine, KOKORO_VOICES
from book_parser import BookParser
from packager import get_audio_duration_seconds
from synthesizer import SynthesisManager, transcript_path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "output"
PREVIEWS_DIR = STORAGE_DIR / "previews"
STATIC_DIR = BASE_DIR / "static"
MOBILE_DIR = BASE_DIR / "mobile" / "web"

for d in [STORAGE_DIR, UPLOADS_DIR, OUTPUT_DIR, PREVIEWS_DIR, STATIC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BookForge - Book to Audiobook Compiler", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State stores
parsed_books: Dict[str, Dict[str, Any]] = {}
manager = SynthesisManager(str(STORAGE_DIR))

def get_local_ip() -> str:
    """Find the best local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_qr_base64(url: str) -> str:
    """Generate a base64 encoded PNG data URL for a given URL."""
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#ffffff")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

STARTED_AT = time.time()

@app.get("/api/network-info")
async def get_network_info():
    ip = get_local_ip()
    port = 8000
    url = f"http://{ip}:{port}"
    app_url = f"{url}/app/"
    return {
        "ip": ip,
        "port": port,
        "url": url,
        "app_url": app_url,
        "qr_code": generate_qr_base64(app_url),   # the phone opens the phone app, not this dashboard
        "gpu_available": kokoro_engine.device == "cuda"
    }

@app.get("/api/server-info")
async def get_server_info():
    """Everything the PC dashboard shows about this machine."""
    import torch
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    free = total = None
    if gpu:
        try:
            free, total = torch.cuda.mem_get_info()
        except Exception:
            pass
    return {
        "device": kokoro_engine.device,
        "gpu_name": gpu,
        "gpu_mem_free_mb": round(free / 1048576) if free else None,
        "gpu_mem_total_mb": round(total / 1048576) if total else None,
        "engine_loaded": bool(kokoro_engine._pipelines),
        "uptime_sec": round(time.time() - STARTED_AT),
        "books_in_memory": len(parsed_books),
    }

@app.get("/api/jobs")
async def list_jobs():
    """All jobs since the server started, newest first (with the full log)."""
    out = []
    for job in manager.jobs.values():
        d = job.to_dict()
        d["logs"] = job.logs[-60:]
        d["start_time"] = getattr(job, "start_time", None)
        out.append(d)
    out.sort(key=lambda j: j.get("start_time") or 0, reverse=True)
    return out

@app.get("/api/voices")
async def list_voices():
    """List all available Kokoro voices + edge-tts option."""
    return {
        "engine": "kokoro",
        "device": kokoro_engine.device,
        "kokoro_voices": KOKORO_VOICES,
        "edge_voices": [
            {"id": "en-US-ChristopherNeural", "name": "Christopher (US Male - Cloud)", "gender": "Male", "accent": "American"},
            {"id": "en-US-GuyNeural", "name": "Guy (US Male - Cloud)", "gender": "Male", "accent": "American"},
            {"id": "en-US-JennyNeural", "name": "Jenny (US Female - Cloud)", "gender": "Female", "accent": "American"},
            {"id": "en-GB-RyanNeural", "name": "Ryan (UK Male - Cloud)", "gender": "Male", "accent": "British"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (UK Female - Cloud)", "gender": "Female", "accent": "British"}
        ]
    }

@app.get("/api/voices/preview/{voice_id}")
async def get_voice_preview(voice_id: str):
    """Serve or generate a preview audio sample for a voice."""
    try:
        preview_file = await kokoro_engine.get_or_create_voice_preview(voice_id, str(PREVIEWS_DIR))
        return FileResponse(preview_file, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {e}")

@app.post("/api/upload")
async def upload_book(file: UploadFile = File(...)):
    """Handle book upload from phone or PC, parse metadata & chapters."""
    filename = file.filename or "book.epub"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".epub", ".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail="Unsupported format. Please upload .epub, .pdf, or .txt")

    dest_path = UPLOADS_DIR / filename
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        book_data = BookParser.parse_book(str(dest_path), str(UPLOADS_DIR))
        book_id = book_data["book_id"]
        parsed_books[book_id] = book_data
        return book_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to parse book: {e}")

@app.get("/api/books/{book_id}")
async def get_book_details(book_id: str):
    if book_id not in parsed_books:
        raise HTTPException(status_code=404, detail="Book not found")
    return parsed_books[book_id]

@app.get("/api/books/{book_id}/cover")
async def get_book_cover(book_id: str):
    book = parsed_books.get(book_id)
    if not book or not book.get("cover_path") or not os.path.exists(book["cover_path"]):
        raise HTTPException(status_code=404, detail="Cover not found")
    media_type = "image/png" if book["cover_path"].lower().endswith(".png") else "image/jpeg"
    return FileResponse(book["cover_path"], media_type=media_type)

@app.post("/api/compile")
async def start_compilation(
    book_id: str = Form(...),
    voice: str = Form("af_heart"),
    engine: str = Form("kokoro"),
    speed: float = Form(1.0),
    output_format: str = Form("m4b"),
    selected_chapters: Optional[str] = Form(None) # JSON array of chapter ids
):
    book = parsed_books.get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found. Please upload first.")

    chap_ids = None
    if selected_chapters:
        try:
            chap_ids = json.loads(selected_chapters)
        except Exception:
            chap_ids = None

    job = manager.create_job(
        book=book,
        voice=voice,
        engine=engine,
        speed=speed,
        output_format=output_format,
        selected_chapter_ids=chap_ids
    )
    manager.start_job(job.job_id)
    return job.to_dict()

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()

@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.cancel()
    return {"status": "cancelled"}

@app.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(websocket: WebSocket, job_id: str):
    """WebSocket streaming real-time job progress to phone UI."""
    await websocket.accept()
    job = manager.get_job(job_id)
    if not job:
        await websocket.send_json({"error": "Job not found"})
        await websocket.close()
        return

    try:
        while True:
            data = job.to_dict()
            await websocket.send_json(data)
            if job.status in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(0.4)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.get("/api/audiobooks")
async def list_audiobooks():
    """List all compiled audiobooks in storage/output."""
    results = []
    for item in OUTPUT_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in [".m4b", ".zip", ".mp3"]:
            size_mb = item.stat().st_size / (1024 * 1024)
            dur_sec = get_audio_duration_seconds(str(item)) if item.suffix.lower() in [".m4b", ".mp3"] else 0.0
            results.append({
                "filename": item.name,
                "title": item.stem,
                "format": item.suffix.lstrip(".").lower(),
                "size_mb": round(size_mb, 1),
                "duration_sec": round(dur_sec, 0),
                "created_at": item.stat().st_mtime,
                "has_text": os.path.exists(transcript_path(str(item))),
            })
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return results

@app.get("/api/download/{filename}")
async def download_audiobook(filename: str):
    """Trigger browser file download on phone to save file to phone storage."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audiobook not found")

    media_type = "audio/mp4" if filename.lower().endswith(".m4b") else "application/zip"
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/stream/{filename}")
async def stream_audiobook(filename: str):
    """Stream audio for in-browser mobile player with Range request support."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audiobook not found")
    media_type = "audio/mp4" if filename.lower().endswith(".m4b") else "audio/mpeg"
    return FileResponse(str(file_path), media_type=media_type)

@app.get("/api/transcript/{filename}")
async def get_transcript(filename: str):
    """Read-along text: {chapters: [{title, start, para}], paras: [[[word, start, end], ...], ...]}."""
    file_path = OUTPUT_DIR / Path(filename).name
    text = Path(transcript_path(str(file_path)))
    if not text.exists():
        raise HTTPException(status_code=404, detail="This book has no read-along text")
    return FileResponse(str(text), media_type="application/json")

@app.delete("/api/audiobooks/{filename}")
async def delete_audiobook(filename: str):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        file_path.unlink()
        text = Path(transcript_path(str(file_path)))
        if text.exists():
            text.unlink()
        return {"success": True}
    raise HTTPException(status_code=404, detail="File not found")

# PC dashboard (static/) and phone app (mobile/)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/app")
async def app_no_slash():
    return RedirectResponse("/app/")

app.mount("/app", StaticFiles(directory=str(MOBILE_DIR), html=True), name="mobile")

@app.get("/")
async def root(request: Request):
    # the dashboard is for the PC itself — anything else (a phone) gets the phone app
    host = request.client.host if request.client else ""
    if host not in ("127.0.0.1", "::1", "localhost", "testclient") and host != get_local_ip():
        return RedirectResponse("/app/")
    return FileResponse(str(STATIC_DIR / "index.html"))
