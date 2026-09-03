import subprocess
import threading
import time
import os

active_timers = []

def _timer_worker(seconds: int, label: str):
    time.sleep(seconds)
    # Sound alarm and speak
    try:
        subprocess.run(["osascript", "-e", "display notification \"Timer Completed!\" with title \"J.A.R.V.I.S. Timer\""], check=False)
        # Play alarm sound
        for _ in range(2):
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
            time.sleep(0.3)
    except Exception:
        pass
    
    from voice import speak
    speak(f"Sir, your timer for {label} has expired.", async_mode=True)

def set_timer(duration_seconds: int = 180, label: str = "Timer") -> dict:
    """
    Sets a countdown timer for a specified number of seconds (e.g. 180 for 3 minutes).
    Alerts the user with a chime and voice announcement when finished.
    """
    mins = duration_seconds // 60
    secs = duration_seconds % 60
    
    time_desc = []
    if mins > 0:
        time_desc.append(f"{mins} minute" + ("s" if mins > 1 else ""))
    if secs > 0:
        time_desc.append(f"{secs} second" + ("s" if secs > 1 else ""))
    time_str = " and ".join(time_desc) if time_desc else f"{duration_seconds} seconds"

    t = threading.Thread(target=_timer_worker, args=(duration_seconds, label or time_str), daemon=True)
    t.start()
    active_timers.append(t)

    return {
        "status": "success",
        "duration_seconds": duration_seconds,
        "label": label,
        "detail": f"Timer set for {time_str}, Sir. I will notify you the moment it elapses."
    }
