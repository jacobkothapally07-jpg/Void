import os
import time
import json
import urllib.request
import urllib.parse
import ssl
import subprocess
import threading
import re

from tools.system_tools import get_system_health, control_mac_settings
from brain.fast_engine import dispatch_fast_action

NTFY_CMD_TOPIC = os.getenv("NTFY_REMOTE_CMD", "jk_cmd_529d6dbeda151fd6ff6b2146f3c593d4")
NTFY_REPLY_TOPIC = os.getenv("NTFY_REMOTE_REPLY", "jk_reply_c20c924a97e53fc63041ff3d391f2a38")

def ensure_cloudflared_tunnel(local_port=8080):
    """Starts cloudflared quick tunnel to expose the web HUD via a secure HTTPS link."""
    for p in ["/opt/homebrew/bin", "/usr/local/bin"]:
        if p not in os.environ.get("PATH", ""):
            os.environ["PATH"] = p + ":" + os.environ.get("PATH", "")

    # Check if cloudflared is already running
    try:
        out = subprocess.run(["pgrep", "-f", "cloudflared tunnel"], capture_output=True, text=True)
        if out.returncode == 0:
            if os.path.exists("/tmp/jarvis_remote_url.txt"):
                with open("/tmp/jarvis_remote_url.txt") as f:
                    url = f.read().strip()
                if url:
                    print(f"\033[96m[Pocket JARVIS HTTPS Web Remote] {url}/remote\033[0m")
                    return url
    except Exception:
        pass

    try:
        import shutil
        cloudflared_path = shutil.which("cloudflared") or "/opt/homebrew/bin/cloudflared"
        if not os.path.exists(cloudflared_path):
            return None
        
        log_file = open("/tmp/cloudflared.log", "w")
        proc = subprocess.Popen(
            [cloudflared_path, "tunnel", "--url", f"http://127.0.0.1:{local_port}"],
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
        url = None
        for _ in range(16):
            time.sleep(0.5)
            if os.path.exists("/tmp/cloudflared.log"):
                with open("/tmp/cloudflared.log") as f:
                    content = f.read()
                m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
                if m:
                    url = m.group(0)
                    with open("/tmp/jarvis_remote_url.txt", "w") as f:
                        f.write(url)
                    print(f"\033[96m[Pocket JARVIS HTTPS Web Remote] {url}/remote\033[0m")
                    print(f"\033[92m[Permanent GitHub Pages URL] https://jacobkothapally07-jpg.github.io/jarvis/\033[0m")
                    return url
    except Exception as e:
        print(f"[Pocket JARVIS Tunnel] {e}")
    return None

def _get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def send_phone_reply(text: str, title: str = "J.A.R.V.I.S.", tags: str = "robot"):
    """Sends a text notification back to the user's phone via ntfy.sh."""
    url = f"https://ntfy.sh/{NTFY_REPLY_TOPIC}"
    try:
        req = urllib.request.Request(
            url,
            data=text.encode("utf-8"),
            headers={
                "Title": title,
                "Tags": tags,
                "Priority": "default",
                "User-Agent": "JARVIS-Remote/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8.0, context=_get_ssl_context()) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Pocket JARVIS Reply Error] {e}")
        return False

def send_phone_photo(image_path: str, title: str = "Workstation Snapshot", filename: str = "snapshot.jpg"):
    """Sends an image file directly to the user's phone notification."""
    if not os.path.exists(image_path):
        return False
        
    url = f"https://ntfy.sh/{NTFY_REPLY_TOPIC}"
    try:
        with open(image_path, "rb") as f:
            data = f.read()
            
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Title": title,
                "Filename": filename,
                "Tags": "camera,desktop",
                "Priority": "default",
                "User-Agent": "JARVIS-Remote/1.0"
            },
            method="PUT"
        )
        with urllib.request.urlopen(req, timeout=12.0, context=_get_ssl_context()) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Pocket JARVIS Photo Error] {e}")
        return False

def handle_remote_command(command_text: str):
    """Parses and executes a command received remotely from the user's phone."""
    clean = command_text.strip()
    lower = clean.lower()
    print(f"\n\033[95m[Pocket JARVIS Command Received]\033[0m \"{clean}\"")

    # 1. Desktop Screenshot
    if any(k in lower for k in ["screenshot", "screen", "snap", "desktop photo", "see screen"]):
        snap_path = "/tmp/pocket_jarvis_screen.jpg"
        subprocess.run(["screencapture", "-x", snap_path], check=False)
        # Fast native compression down to ~200KB for instant mobile delivery
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "65", "-Z", "1280", snap_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Auto-archive to user's Pictures folder
        archive_dir = os.path.expanduser("~/Pictures/JARVIS_Sentry")
        os.makedirs(archive_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        subprocess.run(["cp", snap_path, os.path.join(archive_dir, f"Screen_{ts}.jpg")], check=False)

        send_phone_photo(snap_path, title="Workstation Screen Capture", filename="screen.jpg")
        send_phone_reply("Here is the current live view of your workstation display, Sir.", title="Screen Captured", tags="desktop")
        return

    # 2. FaceTime HD Camera (Desk / Sentry View)
    if any(k in lower for k in ["camera", "desk", "sentry", "webcam", "see desk"]):
        cam_path = "/tmp/pocket_jarvis_cam.jpg"
        sentry_bin = os.path.expanduser("~/.gemini/antigravity/scratch/jarvis/native_hud/SentryEye")
        if os.path.exists(sentry_bin):
            subprocess.run([sentry_bin, cam_path], check=False)
            if os.path.exists(cam_path):
                subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "70", "-Z", "1280", cam_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Auto-archive to user's Pictures folder
                archive_dir = os.path.expanduser("~/Pictures/JARVIS_Sentry")
                os.makedirs(archive_dir, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                subprocess.run(["cp", cam_path, os.path.join(archive_dir, f"Sentry_{ts}.jpg")], check=False)

                send_phone_photo(cam_path, title="Workstation Desk View", filename="desk.jpg")
                send_phone_reply("Here is the live camera feed of your desk, Sir.", title="Desk Vision", tags="camera")
                return
        send_phone_reply("Could not access camera module, Sir.", title="Camera Error", tags="warning")
        return

    # 3. Lock Workstation
    if any(k in lower for k in ["lock", "lock mac", "lock down", "secure mac"]):
        control_mac_settings("lock")
        send_phone_reply("Workstation locked down successfully, Sir.", title="Security Locked", tags="lock")
        return

    # 4. Battery & Health
    if any(k in lower for k in ["battery", "health", "system", "stats"]):
        h = get_system_health()
        batt = h.get("battery", {})
        msg = f"Battery: {batt.get('percent', '100%')} ({batt.get('power_source', 'AC Power')}) | CPU: {h.get('cpu_usage_percent', 0)}%"
        send_phone_reply(msg, title="System Health", tags="battery")
        return

    # 5. Sleep / Wake / Standby
    if any(k in lower for k in ["sleep display", "sleep mac", "put mac to sleep", "sleep workstation", "sleep", "standby"]):
        control_mac_settings("sleep_display")
        from voice_listener import set_jarvis_sleeping
        set_jarvis_sleeping(True)
        send_phone_reply("Mac display sleeping and J.A.R.V.I.S. placed on low-power standby, Sir.", title="System Sleeping", tags="moon,zzz")
        return

    if any(k in lower for k in ["wake", "wake up"]):
        from voice_listener import set_jarvis_sleeping
        set_jarvis_sleeping(False)
        send_phone_reply("Online and operational on your Mac, Sir.", title="Systems Active", tags="zap")
        return

    # 5b. Master Volume Control
    m_vol = re.search(r'(?:vol|volume)\s*(?:to\s*|set\s*)?(\d+)', lower)
    if m_vol:
        val = int(m_vol.group(1))
        from tools.system_tools import set_mac_volume
        set_mac_volume(val)
        send_phone_reply(f"Master volume adjusted to {val}%, Sir.", title="Volume", tags="sound")
        return

    # 6. Fast Action Dispatch
    matched, fast_reply = dispatch_fast_action(clean)
    if matched and fast_reply:
        send_phone_reply(fast_reply, title="J.A.R.V.I.S.", tags="robot")
        return

    # 7. Deep Brain / Gemini Intelligence Fallback
    try:
        from brain import JarvisBrain
        brain = JarvisBrain()
        reply = brain.respond(clean)
        send_phone_reply(reply, title="J.A.R.V.I.S.", tags="speech_balloon")
    except Exception as e:
        send_phone_reply(f"Command acknowledged, Sir ({str(e)}).", title="J.A.R.V.I.S.", tags="warning")

def run_pocket_bridge():
    """Continuously listens for commands sent from the user's phone via ntfy.sh."""
    print(f"\033[95m[Pocket JARVIS Bridge Active]\033[0m Listening on https://ntfy.sh/{NTFY_CMD_TOPIC}...")
    
    # Expose secure worldwide HTTPS endpoint for mobile web HUD
    ensure_cloudflared_tunnel()

    ctx = _get_ssl_context()
    url = f"https://ntfy.sh/{NTFY_CMD_TOPIC}/raw"

    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Mac-Bridge"})
            with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
                while True:
                    line = resp.readline()
                    if not line:
                        break
                    text = line.decode("utf-8").strip()
                    if text:
                        threading.Thread(target=handle_remote_command, args=(text,), daemon=True).start()
        except Exception as e:
            time.sleep(3.0)

if __name__ == "__main__":
    run_pocket_bridge()
