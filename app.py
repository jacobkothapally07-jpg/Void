import os
import sys
import subprocess
import threading
import socketserver
import json
import time
import signal
import ssl
import urllib.request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hud import JarvisHTTPHandler, PORT
from voice import speak

actual_port = 8080
httpd = None
last_cloud_wakeup_time = 0

def subscribe_cloud_wakeup():
    """Listens to global cloud wakeup signals from iPhone/Siri (ntfy.sh/jk_jarvis_wakeup)."""
    global last_cloud_wakeup_time
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    print("[JK Cloud Bridge] Remote phone wakeup listener active (ntfy.sh/jk_jarvis_wakeup)...")
    while True:
        try:
            req = urllib.request.Request("https://ntfy.sh/jk_jarvis_wakeup/raw", headers={"User-Agent": "JARVIS-Mac"})
            with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
                while True:
                    line = resp.readline()
                    if not line:
                        break
                    text = line.decode("utf-8").strip()
                    if text:
                        now = time.time()
                        if now - last_cloud_wakeup_time < 5:
                            continue
                        last_cloud_wakeup_time = now
                        
                        print(f"\033[92m[Phone Wakeup Received]\033[0m {text}")
                        try:
                            subprocess.run(["osascript", "-e", "set volume output volume 80", "-e", "set volume without output muted"], check=False)
                            from hud import launch_hud_window
                            launch_hud_window(actual_port)
                        except Exception:
                            pass
                        
                        speak("Neural matrix online and active on your workstation, Sir. At your service.", async_mode=True)
        except Exception as e:
            time.sleep(2)

def setup_app_profile(profile_dir, port):
    default_dir = os.path.join(profile_dir, "Default")
    os.makedirs(default_dir, exist_ok=True)
    pref_file = os.path.join(default_dir, "Preferences")
    
    prefs = {
        "profile": {
            "content_settings": {
                "exceptions": {
                    "media_stream_mic": {
                        f"http://127.0.0.1:{port},*": {"setting": 1},
                        "http://127.0.0.1:8080,*": {"setting": 1},
                        "http://127.0.0.1:8081,*": {"setting": 1},
                        "http://127.0.0.1:8082,*": {"setting": 1}
                    }
                }
            },
            "default_content_setting_values": {
                "media_stream_mic": 1,
                "notifications": 1
            }
        }
    }
    try:
        with open(pref_file, "w") as f:
            json.dump(prefs, f)
    except Exception:
        pass

def launch_chrome_app(url):
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    profile_dir = os.path.expanduser("~/.jarvis_chrome_app_profile")
    os.makedirs(profile_dir, exist_ok=True)
    setup_app_profile(profile_dir, actual_port)

    flags = [
        chrome_path,
        f"--app={url}",
        f"--user-data-dir={profile_dir}",
        "--use-fake-ui-for-media-stream",
        "--autoplay-policy=no-user-gesture-required",
        "--enable-features=OverlayScrollbar",
        "--window-size=1150,850",
        "--no-first-run",
        "--no-default-browser-check"
    ]

    try:
        return subprocess.Popen(flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        subprocess.run(["open", url], check=False)
        return None

def start_daemon_server():
    global httpd, actual_port
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    
    for p in range(8080, 8090):
        try:
            httpd = socketserver.ThreadingTCPServer(("0.0.0.0", p), JarvisHTTPHandler)
            actual_port = p
            break
        except OSError:
            continue

    if not httpd:
        print("[JARVIS] Could not bind to port 8080-8090.")
        sys.exit(1)

    print(f"\033[92m[JARVIS Daemon] Listening on http://127.0.0.1:{actual_port}\033[0m")
    
    # Start Cloud Bridge Wakeup listener for iPhone / Siri
    t_cloud = threading.Thread(target=subscribe_cloud_wakeup, daemon=True)
    t_cloud.start()

    httpd.serve_forever()

if __name__ == "__main__":
    if "--gui" in sys.argv:
        try:
            import urllib.request
            req = urllib.request.urlopen("http://127.0.0.1:8080/api/stats", timeout=0.8)
            launch_chrome_app("http://127.0.0.1:8080")
            sys.exit(0)
        except Exception:
            pass

        t = threading.Thread(target=start_daemon_server, daemon=True)
        t.start()
        time.sleep(0.8)
        proc = launch_chrome_app(f"http://127.0.0.1:{actual_port}")
        if proc:
            proc.wait()
    else:
        start_daemon_server()
