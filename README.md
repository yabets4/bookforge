# ⚡ BookForge — Book to Audiobook GPU Compiler 📖🔊

> **Transform books (EPUB, PDF, TXT) into rich neural audiobooks using your PC's GPU, and save them straight to your phone.**  
> Powered by **Kokoro-82M (CUDA)**, **FastAPI**, and **Capacitor**. Zero cloud subscription fees, 100% private.

[![License](https://img.shields.io/badge/License-Apache%202.0%20%2F%20MIT-green.svg)](#)
[![Model](https://img.shields.io/badge/TTS%20Model-Kokoro--82M%20(PyTorch%20CUDA)-orange.svg)](https://huggingface.co/hexgrad/Kokoro-82M)
[![Framework](https://img.shields.io/badge/Platform-Windows%20PC%20%2B%20Android-blue.svg)](#)
[![Prebuilt APK](https://img.shields.io/badge/Download-BookForge.apk%20(3.9%20MB)-success.svg)](BookForge.apk)

---

## 🌟 Why BookForge?

Running neural speech models directly on mobile phone hardware burns battery, stutters, and limits quality.  
**BookForge flips the script:**
- **Your PC acts as the high-powered GPU Compiler**: Synthesizes speech using Kokoro-82M on your desktop NVIDIA GPU at ~0.39s per sentence.
- **Your Phone acts as the remote controller & player**: Pick books, audition voices, watch live chapter-by-chapter synthesis progress over Wi-Fi, and download the finished `.m4b` directly to your phone's storage.

```
       📱 Mobile App / Phone Browser (Remote & Player)
                           ▲   │
         1. Send Book File │   │ 3. One-Tap Save to Phone (.m4b)
                           │   ▼
    ========================================================
       💻 PC Server (:8000) — GPU Compiler
          • PyMuPDF & EbookLib  → Chapter & Cover Extractor
          • Kokoro-82M (CUDA)   → GPU Speech Synthesis
          • FFmpeg 7.1          → M4B AAC Muxer & Chapter Marker
    ========================================================
```

---

## ✨ Features

- **🧠 GPU-Accelerated Kokoro-82M Synthesis**: High-speed, natural neural voice narration running locally on NVIDIA CUDA.
- **🎙️ 30+ Expressive Voices**: Select from popular voices (`af_heart`, `am_michael`, `bf_alice`, `bm_george`, etc.) with instant audio previews.
- **📄 Smart Multi-Format Parsing**:
  - **EPUB**: Extracts chapters, clean HTML, metadata, and embedded book covers.
  - **PDF**: Uses PyMuPDF (`fitz`) for rapid text extraction, chapter detection, and cover generation.
  - **TXT / Markdown**: Automatic chapter header splitting.
- **🎧 True M4B Audiobooks with Chapters**: Generates standard `.m4b` files with embedded chapter markers (so you can jump chapters in apps like Smart AudioBook Player, Voice, Sirin, and Apple Books).
- **📱 Zero-Config Phone Connection**: When started on the PC, an ASCII QR code is displayed right in the terminal. Scan with your phone camera to connect immediately.
- **📲 Dedicated Android App**: Ready-to-use Capacitor mobile app included, with pre-compiled [`BookForge.apk`](BookForge.apk).
- **🎶 Built-in Offline Web Player**: Integrated audio player supporting Android lockscreen playback controls (MediaSession API).

---

## 🚀 Quick Start (PC Compiler Server)

### Prerequisites
- Windows 10/11 with Python 3.9+
- NVIDIA GPU with CUDA support (or CPU fallback)

### 1. Install Dependencies
```bash
git clone https://github.com/yabets4/bookforge.git
cd bookforge
pip install -r requirements.txt
```

### 2. Run Compiler Server
```bash
python run.py
```
*(Or double-click `run.bat`)*

You will see the network address and a terminal QR code:
```
============================================================
  ⚡ BookForge — Book to Audiobook GPU Compiler 📖🔊
============================================================
  • PC Browser:     http://localhost:8000
  • Phone Browser:  http://192.168.240.131:8000
============================================================
  📱 SCAN WITH YOUR PHONE TO OPEN INSTANTLY:
  [QR CODE]
```

---

## 📱 Mobile Setup (Android)

### Option A: Direct APK Sideload (Recommended)
1. Download [**`BookForge.apk`**](BookForge.apk) (3.9 MB) onto your Android phone.
2. Install and launch the app.
3. Tap the server badge to connect to your PC's Wi-Fi IP.

### Option B: Mobile Browser / PWA (Zero Install)
1. Connect your phone to the same Wi-Fi network as your PC.
2. Scan the terminal QR code or navigate to `http://<your-pc-ip>:8000` in Chrome/Safari.
3. (Optional) Tap **"Add to Home Screen"** to run fullscreen.

---

## 📦 Project Structure

```
bookforge/
├── run.py                 # Startup script: Wi-Fi IP detection & terminal QR code
├── run.bat                # Windows 1-click launcher
├── server.py              # FastAPI application with REST & WebSocket endpoints
├── kokoro_engine.py       # Kokoro-82M GPU inference engine (PyTorch CUDA)
├── synthesizer.py         # Multi-engine job manager & progress streaming
├── book_parser.py         # Resilient EPUB, PDF, and TXT parser
├── packager.py            # FFmpeg M4B / MP3 packager with chapter markers & tags
├── requirements.txt       # Python dependencies
├── BookForge.apk          # Prebuilt Android APK
├── static/                # Responsive mobile-first dashboard assets
├── mobile/                # Capacitor Android native companion source
│   ├── capacitor.config.json
│   └── android/           # Native Gradle project
└── storage/               # Uploads and compiled output
```

---

## 📄 License

MIT / Apache 2.0
