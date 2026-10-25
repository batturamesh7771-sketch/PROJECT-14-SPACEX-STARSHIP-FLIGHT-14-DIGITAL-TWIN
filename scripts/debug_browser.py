import subprocess
import time
import json
import urllib.request

def main():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        "http://127.0.0.1:8080/"
    ])
    try:
        time.sleep(2)
        # Fetch targets from CDP
        resp = urllib.request.urlopen("http://127.0.0.1:9222/json")
        targets = json.loads(resp.read().decode())
        print("CDP Targets:", len(targets))
        for t in targets:
            print(" -", t.get("title"), "|", t.get("url"))
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    main()
