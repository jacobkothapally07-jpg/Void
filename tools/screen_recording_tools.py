import subprocess
import os
import signal
import time
import datetime

_recording_process = None
_recording_file = None

def start_screen_recording(duration_seconds: int = None) -> dict:
    """
    Starts high-definition screen video recording on macOS using native screencapture.
    Saves the video directly to the user's Desktop.
    """
    global _recording_process, _recording_file
    
    if _recording_process and _recording_process.poll() is None:
        return {
            "status": "warning",
            "message": f"Screen recording is already in progress, Sir: {_recording_file}",
            "detail": f"Screen recording is already active, Sir. File is saving to {_recording_file}."
        }
        
    desktop_dir = os.path.expanduser("~/Desktop")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    _recording_file = os.path.join(desktop_dir, f"JARVIS_Recording_{timestamp}.mov")
    
    cmd = ["screencapture", "-v", _recording_file]
    if duration_seconds and duration_seconds > 0:
        cmd.extend(["-V", str(duration_seconds)])
        
    try:
        _recording_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return {
            "status": "success",
            "file": _recording_file,
            "detail": f"Screen recording initiated, Sir. Capturing your display to Desktop."
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "detail": f"Failed to start screen recording: {e}"}

def stop_screen_recording() -> dict:
    """
    Stops the active screen recording and reveals the video file in Finder.
    """
    global _recording_process, _recording_file
    
    # Try stopping native screencapture
    stopped = False
    if _recording_process and _recording_process.poll() is None:
        try:
            _recording_process.send_signal(signal.SIGINT)
            _recording_process.wait(timeout=3)
            stopped = True
        except Exception:
            _recording_process.kill()
            stopped = True
            
    # Also stop any system screencapture -v processes
    try:
        subprocess.run(["pkill", "-INT", "-f", "screencapture -v"], check=False)
        stopped = True
    except Exception:
        pass
        
    saved_path = _recording_file or os.path.expanduser("~/Desktop")
    _recording_process = None
    
    # Reveal file in Finder
    if _recording_file and os.path.exists(_recording_file):
        try:
            subprocess.run(["open", "-R", _recording_file], check=False)
        except Exception:
            pass
            
    return {
        "status": "success",
        "file": saved_path,
        "detail": f"Screen recording stopped and saved to your Desktop, Sir."
    }
