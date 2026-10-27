# BookForge API — for the phone app

Base URL: `http://<PC-IP>:8000` (PC and phone on same Wi-Fi). CORS open, no auth.
Get the PC IP from the `run.py` banner, or `GET /api/network-info` once known.

## Flow

1. `POST /api/upload` — multipart, field `file` (`.pdf` `.epub` `.txt` `.md`)
   → `{ book_id, title, author, format, total_words, total_characters, estimated_duration_sec, chapters: [{ id, title, word_count, char_count, text, selected }] }`
   (`chapters[].text` is the full text — big for a long book; ignore it if you only need titles.)
2. `POST /api/compile` — form fields:
   - `book_id` (required)
   - `voice` = `af_heart` (list: `GET /api/voices` → `kokoro_voices[].id`)
   - `engine` = `kokoro` (GPU, offline) | `edge` (cloud voices, `edge_voices[].id`)
   - `speed` = `1.0`
   - `output_format` = `m4b` (one file, chapters) | anything else → `.zip` of per-chapter mp3s
   - `selected_chapters` = JSON array of chapter ids, e.g. `[0,1,2]` (omit = all)
   → job object (below)
3. Progress — either:
   - poll `GET /api/jobs/{job_id}`, or
   - WebSocket `ws://<PC-IP>:8000/ws/jobs/{job_id}` — job object every 0.4 s, closes when done
4. `GET /api/download/{output_file}` — the finished audiobook (attachment). Save it on the phone.

## Job object

```
{ job_id, book_id, book_title, book_author, voice, engine, speed, output_format,
  status,            // queued | running | packaging | completed | failed | cancelled
  progress,          // 0–100
  current_chapter_title, current_chapter_index, total_chapters,
  elapsed_seconds, eta_seconds, error_message,
  output_file,       // filename to download, set when completed
  output_size_bytes, recent_logs }
```

## Other endpoints

| | |
|---|---|
| `POST /api/jobs/{job_id}/cancel` | stop a job |
| `GET /api/audiobooks` | finished books: `[{ filename, title, format, size_mb, duration_sec, created_at }]` |
| `GET /api/stream/{filename}` | stream instead of download (supports seeking) |
| `DELETE /api/audiobooks/{filename}` | delete from PC |
| `GET /api/books/{book_id}/cover` | cover image |
| `GET /api/voices/preview/{voice_id}` | short mp3 sample |
| `GET /api/jobs` | all jobs since the server started (PC dashboard) |
| `GET /api/server-info` | GPU, memory, uptime (PC dashboard) |

## Pages

- `http://<PC-IP>:8000/` — PC dashboard (QR code, jobs, finished books). Other devices are sent to `/app/`.
- `http://<PC-IP>:8000/app/` — phone app (source in `compiler/mobile/`, all paths relative so it can be bundled into a native app; set the PC address in its Settings).

## Gotchas

- Uploaded books and jobs live in server memory: if the PC server restarts, upload again before compiling. Finished files in `storage/output` stay.
- Android blocks plain `http://` by default — allow cleartext for the PC's IP in the app (e.g. Capacitor `server.cleartext: true` or a network security config).
