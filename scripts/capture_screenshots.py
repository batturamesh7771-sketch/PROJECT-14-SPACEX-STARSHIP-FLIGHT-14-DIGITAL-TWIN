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

def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    artifact_dir = r"C:\Users\user\.gemini\antigravity\brain\3cb4378b-1fb2-42fa-94fb-0fc3e4a81d55"
    os.makedirs(base_dir, exist_ok=True)

    port = get_free_port()
    user_data = tempfile.mkdtemp()
    print(f"Launching Chrome on remote-debugging-port={port}...")
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--use-gl=angle",
        "--use-angle=d3d11",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
        "--window-size=1920,1080",
        "http://127.0.0.1:8080/"
    ])

    s = None
    try:
        # 1. Connect to Chrome CDP
        page_target = None
        for _ in range(30):
            time.sleep(0.5)
            try:
                resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
                targets = json.loads(resp.read().decode())
                page_targets = [t for t in targets if t.get("type") == "page" and "8080" in t.get("url", "")]
                if page_targets:
                    page_target = page_targets[0]
                    print(f"Connected to page target: {page_target.get('url')}")
                    break
            except Exception:
                pass
        assert page_target, "Could not acquire dashboard page target from Chrome"
        ws_url = page_target["webSocketDebuggerUrl"]
        path = "/" + ws_url.split("/", 3)[3]

        s = socket.create_connection(("127.0.0.1", port))
        s.settimeout(4.0)
        assert ws_handshake(s, f"127.0.0.1:{port}", path), "CDP WebSocket Handshake failed"

        # Enable necessary domains
        call_cdp(s, "Page.enable", msg_id=1)
        call_cdp(s, "Runtime.enable", msg_id=2)

        # Set 1920x1080 metrics
        call_cdp(s, "Emulation.setDeviceMetricsOverride", {
            "width": 1920,
            "height": 1080,
            "deviceScaleFactor": 1,
            "mobile": False
        }, msg_id=3)

        # 3. Wait for complete initialization
        print("Waiting for page and simulation initialization...")
        initialized = False
        for attempt in range(50):
            res = call_cdp(s, "Runtime.evaluate", {
                "expression": """
                (function() {
                    return (
                        document.readyState === 'complete' &&
                        window.sceneManager !== undefined &&
                        window.timelineController !== undefined &&
                        window.timelineController.currentProfile !== undefined &&
                        window.hudManager !== undefined
                    );
                })()
                """,
                "returnByValue": True
            }, msg_id=10 + attempt, timeout=2.5)
            val = res.get("result", {}).get("result", {}).get("value") if res else None
            if val is True:
                print(f"Page fully initialized at attempt {attempt}!")
                initialized = True
                break
            elif attempt % 5 == 0:
                print(f"  Attempt {attempt}: res={res}")
            time.sleep(0.5)

        assert initialized, "Page failed to initialize in time"

        # Make sure canvas resize is dispatched
        call_cdp(s, "Runtime.evaluate", {
            "expression": "window.dispatchEvent(new Event('resize')); if (window.sceneManager) window.sceneManager.onWindowResize();",
            "returnByValue": True
        }, msg_id=99)

        # 4. Define all screenshot capture targets
        shots = [
            # 1. Main 3D Cockpit / Mission View (matching Image 1)
            {
                "name": "flight14_cockpit_view.png",
                "view": "vehicle",
                "cam": "MISSION_VIEW",
                "t": 400.0,
                "wait": 3.0
            },
            {
                "name": "flight14_overview_branching.png",
                "view": "vehicle",
                "cam": "MISSION_VIEW",
                "t": 400.0,
                "wait": 3.0
            },
            # 2. Dedicated SpaceX Trajectory Infographic Profile (matching Image 2)
            {
                "name": "flight14_spacex_profile.png",
                "view": "profile",
                "cam": "PROFILE_VIEW",
                "t": 522.0,
                "wait": 3.0
            },
            # 3. 26 Starlinks Deploying Forward from Nosecone Slot with Solar Wings
            {
                "name": "flight14_satellite_forward_deploy.png",
                "view": "vehicle",
                "cam": "CARGO_DEPLOY_CAM",
                "t": 1450.0,
                "wait": 3.0
            },
            {
                "name": "flight14_satellite_deployment.png",
                "view": "vehicle",
                "cam": "DEPLOY_WIDE_CAM",
                "t": 1450.0,
                "wait": 3.0
            },
            # 4. Starship 60 deg Belly-Flop Entry with Hexagonal Tiles and Plasma Shockwave
            {
                "name": "flight14_reentry_belly.png",
                "view": "vehicle",
                "cam": "ENTRY_BELLY",
                "t": 10800.0,
                "wait": 3.0
            },
            # 5. Staging Separation
            {
                "name": "flight14_staging_separation.png",
                "view": "vehicle",
                "cam": "STAGE_SEP",
                "t": 165.0,
                "wait": 3.0
            },
        ]

        msg_counter = 200
        for shot in shots:
            filename = shot["name"]
            out_path = os.path.join(base_dir, filename)
            print(f"\n--- Processing: {filename} (t={shot['t']}, view={shot['view']}, cam={shot['cam']}) ---")

            # Apply state in browser
            setup_code = f"""
            (function() {{
                const targetView = "{shot['view']}";
                const targetCam = "{shot['cam']}";
                const targetT = {shot['t']};

                // View Mode
                const btn = document.querySelector(`.vp-btn[data-view='${{targetView}}']`);
                if (btn) btn.click();

                // Explicit timeline seek
                if (window.timelineController) {{
                    window.timelineController.seekTo(targetT);
                    window.timelineController.isPlaying = false;
                    if (window.timelineController.playBtn) {{
                        window.timelineController.playBtn.innerText = "PLAY";
                        window.timelineController.playBtn.classList.remove("active");
                    }}
                }}

                // Camera mode
                if (window.sceneManager) {{
                    window.sceneManager.setCameraMode(targetCam);
                    window.sceneManager.snapCameraNextFrame = true;
                    window.sceneManager.onWindowResize();
                }}

                // Profile Canvas render if in profile mode
                if (targetView === "profile" && window.spacexProfile) {{
                    window.spacexProfile.resize();
                    window.spacexProfile.updateTime(targetT);
                    window.spacexProfile.render();
                }}

                return {{
                    t: window.timelineController ? window.timelineController.currentTime : -1,
                    view: document.querySelector('.vp-btn.active') ? document.querySelector('.vp-btn.active').dataset.view : null,
                    cam: window.sceneManager ? window.sceneManager.currentCameraMode : null,
                    profDisplay: document.getElementById('spacex-trajectory-profile-view') ? document.getElementById('spacex-trajectory-profile-view').style.display : null
                }};
            }})()
            """
            msg_counter += 1
            eval_res = call_cdp(s, "Runtime.evaluate", {"expression": setup_code, "returnByValue": True}, msg_id=msg_counter)
            applied_state = eval_res.get("result", {}).get("result", {}).get("value") if eval_res else None
            print(f"  Applied state: {applied_state}")

            # Wait for WebGL / 2D Canvas rendering to settle
            time.sleep(shot["wait"])

            # Capture Screenshot
            msg_counter += 1
            cap_res = call_cdp(s, "Page.captureScreenshot", {
                "format": "png",
                "clip": {"x": 0, "y": 0, "width": 1920, "height": 1080, "scale": 1}
            }, msg_id=msg_counter, timeout=15.0)

            if cap_res and "result" in cap_res and "data" in cap_res["result"]:
                b64 = cap_res["result"]["data"]
                decoded = base64.b64decode(b64)
                with open(out_path, "wb") as f_out:
                    f_out.write(decoded)
                print(f"  Saved {out_path} ({len(decoded)} bytes)")

                # Also mirror to brain artifact directory
                if os.path.exists(artifact_dir):
                    art_file = os.path.join(artifact_dir, filename)
                    with open(art_file, "wb") as f_art:
                        f_art.write(decoded)
                    print(f"  Mirrored to artifact: {art_file}")
            else:
                print(f"  ERROR: Screenshot capture failed for {filename}")

        print("\nAll screenshot tasks finished successfully!")

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

if __name__ == "__main__":
    main()
