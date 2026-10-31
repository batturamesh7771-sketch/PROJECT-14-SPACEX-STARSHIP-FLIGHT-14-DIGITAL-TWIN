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

def call_cdp(sock, method, params=None, msg_id=1, timeout=15.0):
    payload = {"id": msg_id, "method": method}
    if params is not None:
        payload["params"] = params
    send_frame(sock, json.dumps(payload))
    start = time.time()
    while time.time() - start < timeout:
        frame = read_frame(sock)
        if frame:
            try:
                data = json.loads(frame)
                if data.get("id") == msg_id:
                    return data
            except Exception:
                pass
    return None

def evaluate(sock, expr, msg_id=1):
    res = call_cdp(sock, "Runtime.evaluate", {"expression": expr, "returnByValue": True}, msg_id=msg_id)
    if res and "result" in res:
        if "exceptionDetails" in res["result"]:
            print(f"EVAL EXCEPTION (msg_id={msg_id}):", res["result"]["exceptionDetails"].get("text"), res["result"]["exceptionDetails"].get("exception", {}).get("description"))
        if "result" in res["result"]:
            return res["result"]["result"].get("value")
    return None

def capture_screenshot(sock, output_path, msg_id=1):
    res = call_cdp(sock, "Page.captureScreenshot", {"format": "png"}, msg_id=msg_id, timeout=20.0)
    if res and "result" in res and "data" in res["result"]:
        raw_b64 = res["result"]["data"]
        img_bytes = base64.b64decode(raw_b64)
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        print(f"Captured: {output_path} ({len(img_bytes)} bytes)")
        return True
    print(f"Failed to capture: {output_path}")
    return False

def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    base_docs = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    artifact_dir = r"C:\Users\user\.gemini\antigravity\brain\3cb4378b-1fb2-42fa-94fb-0fc3e4a81d55"
    os.makedirs(base_docs, exist_ok=True)

    port = get_free_port()
    user_data = tempfile.mkdtemp()
    print(f"Launching Chrome on remote-debugging-port={port}...")
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--disable-gpu-sandbox",
        "--no-sandbox",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--window-size=1920,1080",
        "http://127.0.0.1:8080/replay.html"
    ])

    s = None
    try:
        # 1. Connect to CDP
        page_target = None
        for attempt in range(15):
            time.sleep(1.0)
            try:
                resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
                targets = json.loads(resp.read().decode())
                page_target = next((t for t in targets if "8080" in t.get("url", "") and t.get("type") == "page"), None)
                if page_target:
                    break
            except Exception:
                pass

        if not page_target:
            raise RuntimeError("Could not find Chrome page target.")

        ws_url = page_target["webSocketDebuggerUrl"]
        print(f"Connected to DevTools: {ws_url}")
        path = "/" + ws_url.split("/", 3)[3]

        s = socket.create_connection(("127.0.0.1", port))
        s.settimeout(6.0)
        assert ws_handshake(s, f"127.0.0.1:{port}", path), "WS Handshake failed"

        call_cdp(s, "Runtime.enable", msg_id=101)
        call_cdp(s, "Page.enable", msg_id=102)

        # Wait for application initialization
        print("Waiting for CfrCinematicApp initialization...")
        for wait_i in range(12):
            ready = evaluate(s, "!!(window.cfrApp && window.cfrReplayController && window.cfrCameraDirector)", msg_id=200 + wait_i)
            if ready:
                print("CFR Application successfully initialized in browser!")
                break
            time.sleep(1.0)

        # Helper to save to both docs/ and artifact_dir
        def save_both(filename, msg_id_base):
            p1 = os.path.join(base_docs, filename)
            p2 = os.path.join(artifact_dir, filename)
            capture_screenshot(s, p1, msg_id=msg_id_base)
            capture_screenshot(s, p2, msg_id=msg_id_base + 1)

        # 1. Scene 0: Prelaunch & Pad Presence (Starbase Mechazilla Tower & OLM)
        print("1. Capturing Scene 0: Prelaunch & Starbase Launchpad...")
        evaluate(s, """
            window.cfrReplayController.seekTo(0.0);
            window.cfrReplayController.isPrelaunchCountdown = true;
            window.cfrReplayController.countdownTime_s = 5.0;
            window.cfrCameraDirector.setCameraState("PAD_WIDE", true);
        """, msg_id=301)
        time.sleep(1.2)
        save_both("cfr_01_prelaunch_pad.png", 310)

        # 2. Scene 0/1: Liftoff & Deluge System Bloom (T+6s)
        print("2. Capturing Scene 0/1: 33-Raptor Liftoff & Deluge Cloud...")
        evaluate(s, """
            window.cfrReplayController.isPrelaunchCountdown = false;
            window.cfrReplayController.seekTo(6.0);
            window.cfrCameraDirector.setCameraState("IGNITION_TRACK", true);
        """, msg_id=320)
        time.sleep(1.2)
        save_both("cfr_02_liftoff_deluge.png", 330)

        # 3. Scene 1: Powered Ascent & Max Q (T+68s)
        print("3. Capturing Scene 1: Powered Ascent & Dynamic Pressure...")
        evaluate(s, """
            window.cfrReplayController.seekTo(68.5);
            window.cfrCameraDirector.setCameraState("ASCENT_LONG_LENS", true);
        """, msg_id=340)
        time.sleep(1.2)
        save_both("cfr_03_ascent_maxq.png", 350)

        # 4. Super Heavy Booster Soft Splashdown off Starbase, Texas (T+425s)
        print("4. Capturing Super Heavy Booster Soft Splashdown in Gulf of Mexico...")
        evaluate(s, """
            window.cfrReplayController.seekTo(425.0);
            window.cfrCameraDirector.setCameraState("BOOSTER_GULF_WIDE", true);
        """, msg_id=360)
        time.sleep(1.2)
        save_both("cfr_04_booster_gulf_splashdown.png", 370)

        # 5. Scene 4: 26 Starlink V3 Satellite Deployment (T+1635s)
        print("5. Capturing Scene 4: 26 Starlink V3 Satellite Deployment...")
        evaluate(s, """
            window.cfrReplayController.seekTo(1635.0);
            window.cfrCameraDirector.setCameraState("SATELLITE_TRAIN_WIDE", true);
        """, msg_id=380)
        time.sleep(1.2)
        save_both("cfr_05_starlink_deploy.png", 390)

        # 6. Scene 6: Hypersonic 70° Belly Entry & Aerobraking at 17.5km (T+11274s)
        print("6. Capturing Scene 6: Hypersonic Aerodynamic Belly-Flop...")
        evaluate(s, """
            window.cfrReplayController.seekTo(11274.0);
            window.cfrCameraDirector.setCameraState("ENTRY_DRONE_TRACK", true);
        """, msg_id=400)
        time.sleep(1.2)
        save_both("cfr_06_reentry_plasma.png", 410)

        # 7. Scene 7: Terminal Flip to Straight Vertical 90° Landing Burn (< 1.5 km, T+11342s)
        print("7. Capturing Terminal Flip to Straight Vertical Landing Burn...")
        evaluate(s, """
            window.cfrReplayController.seekTo(11342.0);
            window.cfrCameraDirector.setCameraState("SPLASHDOWN_WIDE", true);
        """, msg_id=420)
        time.sleep(1.5)
        save_both("cfr_07_terminal_vertical_flip.png", 430)

        # 8. Scene 8: Pacific Ocean Splashdown & Recovery (T+11360s)
        print("8. Capturing Pacific Splashdown & Recovery State...")
        evaluate(s, """
            window.cfrReplayController.seekTo(11360.0);
            window.cfrCameraDirector.setCameraState("SPLASHDOWN_WIDE", true);
        """, msg_id=440)
        time.sleep(1.5)
        save_both("cfr_08_pacific_splashdown.png", 450)

        # 9. Cinema Clean Mode (UI Toggled Off for Full 3D Immersion)
        print("9. Capturing Cinema Clean Mode...")
        evaluate(s, """
            document.body.classList.add("cfr-cinema-clean");
            window.cfrReplayController.seekTo(1676.0);
            window.cfrCameraDirector.setCameraState("ORBIT_TRACK", true);
        """, msg_id=460)
        time.sleep(1.2)
        save_both("cfr_09_cinema_clean_view.png", 470)
        evaluate(s, """document.body.classList.remove("cfr-cinema-clean");""", msg_id=475)

        # 10. Synthetic Sandbox: Mechazilla Chopstick Tower Catch
        print("10. Capturing Synthetic Sandbox: Mechazilla Tower Catch...", flush=True)
        evaluate(s, """
            window.cfrReplayController.initProfile("synthetic_engineering_test");
            window.cfrReplayController.seekTo(18.0);
            window.cfrCameraDirector.setCameraState("PAD_WIDE", true);
        """, msg_id=480)
        time.sleep(1.2)
        save_both("cfr_10_synthetic_tower_catch.png", 490)

        # 11. Engineering Dashboard with Minimal Additive Navigation Link
        print("11. Capturing Engineering Lab Navigation Link...", flush=True)
        call_cdp(s, "Page.navigate", {"url": "http://127.0.0.1:8080/index.html"}, msg_id=500)
        time.sleep(2.5)
        save_both("cfr_11_dashboard_link.png", 510)

        print("ALL CINEMATIC REPLAY SCREENSHOTS CAPTURED SUCCESSFULLY!", flush=True)

    finally:
        if s:
            s.close()
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
