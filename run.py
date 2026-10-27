import os
import sys
import socket
import webbrowser
import uvicorn
import qrcode

# Ensure UTF-8 console output for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def get_local_ip() -> str:
    """Detect the local Wi-Fi / LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def print_banner(local_ip: str, port: int):
    local_url = f"http://localhost:{port}"
    network_url = f"http://{local_ip}:{port}/app/"

    print("=" * 60)
    print("  ⚡ BookForge — Book to Audiobook GPU Compiler 📖🔊")
    print("=" * 60)
    print(f"  • PC dashboard:   {local_url}")
    print(f"  • Phone app:      {network_url}")
    print("=" * 60)
    print("  📱 SCAN WITH YOUR PHONE TO OPEN INSTANTLY:")
    print()

    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(network_url)
        qr.print_ascii(invert=True)
    except Exception as e:
        print(f"  (Could not display terminal QR code: {e})")
        print(f"  Open {network_url} in your phone's browser.")

    print()
    print(f"  Make sure your phone is connected to the same Wi-Fi network.")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)
    print()

def main():
    port = 8000
    host = "0.0.0.0"
    local_ip = get_local_ip()

    print_banner(local_ip, port)

    # Automatically open PC browser
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

    uvicorn.run("server:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
