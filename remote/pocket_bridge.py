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

NTFY_CMD_TOPIC = os.getenv("NTFY_REMOTE_CMD", "jk_jarvis_cmd")
NTFY_REPLY_TOPIC = os.getenv("NTFY_REMOTE_REPLY", "jk_jarvis_reply")

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

    # 5. Sleep / Wake
    if any(k in lower for k in ["sleep", "standby"]):
        from voice_listener import set_jarvis_sleeping
        set_jarvis_sleeping(True)
        send_phone_reply("J.A.R.V.I.S. is now in low-power standby mode, Sir.", title="Standby Mode", tags="moon")
        return

    if any(k in lower for k in ["wake", "wake up"]):
        from voice_listener import set_jarvis_sleeping
        set_jarvis_sleeping(False)
        send_phone_reply("Online and operational on your Mac, Sir.", title="Systems Active", tags="zap")
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
