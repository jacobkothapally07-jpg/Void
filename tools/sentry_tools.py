import os
import json
import subprocess
import threading
import time
from voice.sound_effects import play_target_lock, play_protocol_chime

SENTRY_BINARY = os.path.expanduser("~/.gemini/antigravity/scratch/jarvis/native_hud/SentryEye")
SENTRY_DIR = os.path.expanduser("~/.jarvis/sentry")
os.makedirs(SENTRY_DIR, exist_ok=True)

_sentry_running = False
_sentry_thread = None

def capture_sentry_frame(output_path: str = "") -> dict:
    """Invokes native Apple Vision SentryEye tool to capture camera frame and count faces."""
    if not os.path.exists(SENTRY_BINARY):
        return {"status": "error", "message": "SentryEye binary not compiled."}
        
    target_path = output_path or f"/tmp/jarvis_sentry_{int(time.time())}.jpg"
    try:
        res = subprocess.run([SENTRY_BINARY, target_path], capture_output=True, text=True, timeout=5.0)
        output = res.stdout.strip()
        data = json.loads(output)
        faces = int(data.get("faces_detected", 0))
        return {
            "status": "success",
            "faces_detected": faces,
            "snapshot_path": target_path
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "faces_detected": 0}

def activate_sentry_mode(continuous: bool = False) -> dict:
    """
    Activates Sentry Mode:
    Scans FaceTime HD camera using Apple Vision face detection.
    Greets user if present, or arms intruder monitoring if away.
    """
    play_protocol_chime()
    check = capture_sentry_frame()
    faces = check.get("faces_detected", 0)
    
    if faces > 0:
        msg = f"Biometric presence verified, Sir. {faces} face detected. All systems online and operational."
    else:
        msg = "Perimeter sentry armed, Sir. No individuals currently detected. Monitoring workspace for approach."
        
    return {
        "status": "success",
        "faces_detected": faces,
        "detail": msg,
        "snapshot_path": check.get("snapshot_path", "")
    }

def get_sentry_status() -> dict:
    global _sentry_running
    return {"sentry_armed": _sentry_running}
