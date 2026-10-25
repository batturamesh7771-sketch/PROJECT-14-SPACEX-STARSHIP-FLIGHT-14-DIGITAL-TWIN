import subprocess
import time
import json
import urllib.request
import socket
import base64
import os
import struct

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
    print("WS HANDSHAKE RESP:\n", resp[:200])
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
        length = struct.unpack("!H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", sock.recv(8))[0]
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data.extend(chunk)
    return data.decode(errors="ignore")

def main():
    import tempfile
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data = tempfile.mkdtemp()
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data}",
        "http://127.0.0.1:8080/"
    ])
    try:
        time.sleep(2)
        resp = urllib.request.urlopen("http://127.0.0.1:9222/json")
        targets = json.loads(resp.read().decode())
        page_target = next(t for t in targets if "8080" in t.get("url", ""))
        ws_url = page_target["webSocketDebuggerUrl"]
        print("Connecting to:", ws_url)
        # Parse ws url: ws://127.0.0.1:9222/devtools/page/...
        path = "/" + ws_url.split("/", 3)[3]

        s = socket.create_connection(("127.0.0.1", 9222))
        s.settimeout(4.0)
        assert ws_handshake(s, "127.0.0.1:9222", path), "WS Handshake failed"

        # Enable Console and Runtime
        send_frame(s, json.dumps({"id": 1, "method": "Runtime.enable"}))
        send_frame(s, json.dumps({"id": 2, "method": "Console.enable"}))
        
        # Poll window state
        eval_expr = """
        ({
            readyState: document.readyState,
            hasSceneManager: !!window.sceneManager,
            hasTimelineController: !!window.timelineController,
            hasHudManager: !!window.hudManager,
            satellitesInScene: window.sceneManager ? window.sceneManager.satellites.length : 0,
            camMode: window.sceneManager ? window.sceneManager.cameraMode : null
        })
        """
        for poll_id in range(10, 20):
            time.sleep(1.0)
            send_frame(s, json.dumps({
                "id": poll_id,
                "method": "Runtime.evaluate",
                "params": {"expression": eval_expr, "returnByValue": True}
            }))
            got_res = False
            for _ in range(10):
                msg = read_frame(s)
                if not msg:
                    continue
                data = json.loads(msg)
                method = data.get("method", "")
                if "console" in method.lower():
                    print("CONSOLE:", data.get("params", {}).get("message", {}).get("text") or data)
                elif "exception" in method.lower():
                    print("EXCEPTION:", data)
                elif data.get("id") == poll_id:
                    print(f"RAW POLL {poll_id}:", json.dumps(data.get("result", {})))
                    res = data.get("result", {}).get("result", {}).get("value")
                    print(f"POLL {poll_id} RESULT:", json.dumps(res))
                    if res and res.get("hasSceneManager"):
                        got_res = True
                        break
            if got_res:
                break
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
