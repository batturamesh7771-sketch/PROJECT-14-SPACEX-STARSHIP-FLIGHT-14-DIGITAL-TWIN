import subprocess
import time
import json
import urllib.request
import socket
import base64
import os
import struct
import tempfile

def get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def ws_handshake(sock, host, path):
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    sock.sendall(req.encode())
    resp = sock.recv(4096).decode()
    return "101" in resp

def send_frame(sock, text):
    payload = text.encode()
    length = len(payload)
    mask = os.urandom(4)
    masked = bytearray(b ^ mask[i % 4] for i, b in enumerate(payload))
    header = bytearray([0x81])
    if length <= 125:
        header.append(0x80 | length)
    elif length <= 65535:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))
    header.extend(mask)
    sock.sendall(header + masked)

def read_frame(sock):
    try:
        header = sock.recv(2)
    except socket.timeout:
        return None
    except Exception:
        return None
    if not header or len(header) < 2:
        return None
    b2 = header[1]
    length = b2 & 0x7f
    if length == 126:
        raw_len = sock.recv(2)
        while len(raw_len) < 2:
            raw_len += sock.recv(2 - len(raw_len))
        length = struct.unpack("!H", raw_len)[0]
    elif length == 127:
        raw_len = sock.recv(8)
        while len(raw_len) < 8:
            raw_len += sock.recv(8 - len(raw_len))
        length = struct.unpack("!Q", raw_len)[0]
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(min(65536, length - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    return data.decode(errors="ignore")

def capture_url(chrome_path, url, out_png_path, wait_sec=4):
    port = get_free_port()
    user_data = tempfile.mkdtemp()
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--window-size=1920,1080",
        url
    ])
    s = None
    try:
        time.sleep(2.0)
        resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(resp.read().decode())
        page_target = next(t for t in targets if "8080" in t.get("url", ""))
        ws_url = page_target["webSocketDebuggerUrl"]
        path = "/" + ws_url.split("/", 3)[3]

        s = socket.create_connection(("127.0.0.1", port))
        s.settimeout(5.0)
        assert ws_handshake(s, f"127.0.0.1:{port}", path), "WS Handshake failed"

        # Ensure exact URL navigation with full query parameters
        send_frame(s, json.dumps({
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": url}
        }))
        time.sleep(2.5)

        # 1. Force 1920x1080 viewport metrics
        send_frame(s, json.dumps({
            "id": 10,
            "method": "Emulation.setDeviceMetricsOverride",
            "params": {
                "width": 1920,
                "height": 1080,
                "deviceScaleFactor": 1,
                "mobile": False
            }
        }))

        # 2. Trigger window resize for Three.js render sizing
        send_frame(s, json.dumps({
            "id": 11,
            "method": "Runtime.evaluate",
            "params": {"expression": "window.dispatchEvent(new Event('resize')); if (window.sceneManager) window.sceneManager.onWindowResize();"}
        }))

        # 3. Explicitly enforce target time and camera if present in URL
        url_t = None
        url_cam = None
        if "?" in url:
            query = url.split("?", 1)[1]
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            if "t" in params:
                url_t = float(params["t"])
            if "cam" in params:
                url_cam = params["cam"]

        if url_t is not None or url_cam is not None:
            expr = ""
            if url_t is not None:
                expr += f"if (window.timelineController) {{ window.timelineController.seekTo({url_t}); window.timelineController.isPlaying = false; }} "
            if url_cam is not None:
                expr += f"if (window.sceneManager) {{ window.sceneManager.setCameraMode('{url_cam}'); }} "
            send_frame(s, json.dumps({
                "id": 12,
                "method": "Runtime.evaluate",
                "params": {"expression": expr}
            }))

        # Wait for simulation and 3D textures to settle
        time.sleep(wait_sec)

        # Trigger screenshot with explicit 1920x1080 clip
        msg_id = 999
        send_frame(s, json.dumps({
            "id": msg_id,
            "method": "Page.captureScreenshot",
            "params": {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1}
            }
        }))

        # Read frames until we receive response
        for _ in range(50):
            frame = read_frame(s)
            if not frame:
                continue
            data = json.loads(frame)
            if data.get("id") == msg_id:
                b64_data = data.get("result", {}).get("data")
                if b64_data:
                    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)
                    with open(out_png_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    print(f"Captured {out_png_path} ({os.path.getsize(out_png_path)} bytes)")
                    return True
        return False
    finally:
        if s:
            try:
                s.close()
            except Exception:
                pass
        try:
            proc.terminate()
            proc.wait(timeout=2.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))

    shots = [
        ("http://127.0.0.1:8080/?cam=MISSION_VIEW", os.path.join(base_dir, "flight14_overview_branching.png"), 4),
        ("http://127.0.0.1:8080/?t=165&cam=STAGE_SEP", os.path.join(base_dir, "flight14_staging_separation.png"), 4),
        ("http://127.0.0.1:8080/?t=1325&cam=CARGO_DEPLOY_CAM", os.path.join(base_dir, "flight14_satellite_deployment.png"), 4),
        ("http://127.0.0.1:8080/?t=10800&cam=ENTRY_BELLY", os.path.join(base_dir, "flight14_reentry_belly.png"), 4),
    ]

    for url, out_path, wait_s in shots:
        print(f"Capturing: {url} -> {out_path}")
        ok = capture_url(chrome_path, url, out_path, wait_sec=wait_s)
        print("Success:", ok)
        time.sleep(1.0)

if __name__ == "__main__":
    main()
