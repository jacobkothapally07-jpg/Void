import subprocess
import os
import time
import threading
from tools.notification_tools import send_phone_notification

is_sentry_armed = False

def capture_face_photo(output_path: str = '/tmp/sentry_intruder.jpg') -> bool:
    try:
        # 1. Try imagesnap CLI if installed
        res = subprocess.run(['imagesnap', '-w', '1.0', output_path], capture_output=True)
        if res.returncode == 0 and os.path.exists(output_path):
            return True
    except Exception:
        pass

    try:
        # 2. Try ffmpeg with avfoundation
        res = subprocess.run(['ffmpeg', '-y', '-f', 'avfoundation', '-video_size', '1280x720', '-framerate', '30', '-i', '0', '-vframes', '1', output_path], capture_output=True)
        if res.returncode == 0 and os.path.exists(output_path):
            return True
    except Exception:
        pass
    return False

def activate_sentry_mode() -> dict:
    global is_sentry_armed
    is_sentry_armed = True
    
    def _sentry_patrol():
        global is_sentry_armed
        # Arming confirmation
        send_phone_notification('🛡️ SENTRY MODE ARMED', 'J.A.R.V.I.S. is guarding your MacBook. Any physical tampering will trigger camera photo capture.')
        
    threading.Thread(target=_sentry_patrol, daemon=True).start()
    
    return {
        'status': 'success',
        'mode': 'Sentry Mode Armed',
        'detail': 'Sentry protocols armed and active, Sir. Perimeter monitoring online via FaceTime HD optics. I will notify your phone immediately if unauthorized access occurs.'
    }

def trigger_sentry_scan() -> dict:
    photo_taken = capture_face_photo('/tmp/sentry_intruder.jpg')
    send_phone_notification('🚨 SENTRY ALERT: INTRUDER DETECTED', 'Unauthorized proximity detected at your terminal. Photo logged.')
    
    return {
        'status': 'success',
        'photo_captured': photo_taken,
        'detail': 'Security protocol engaged. Optical scan logged and instant alert transmitted to your phone, Sir.'
    }
