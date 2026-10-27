import subprocess
import shutil
import re
import os
import time

_cached_total_mem = None
_cached_cores = None
_last_health = None
_last_health_time = 0

def get_system_health():
    global _cached_total_mem, _cached_cores, _last_health, _last_health_time
    now = time.time()
    if _last_health and (now - _last_health_time < 4.0):
        return _last_health

    health = {"status": "success"}

    # 1. Battery
    try:
        batt_res = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=1)
        batt_out = batt_res.stdout
        pct_match = re.search(r"(\d+)%", batt_out)
        percent = pct_match.group(1) + "%" if pct_match else "N/A"
        health["battery"] = {
            "percent": percent,
            "power_source": "AC Power" if "AC Power" in batt_out else "Battery",
            "is_charging": "charging" in batt_out or "charged" in batt_out
        }
    except Exception:
        health["battery"] = {"percent": "N/A", "is_charging": True}

    # 2. CPU
    try:
        if not _cached_cores:
            _cached_cores = os.cpu_count() or 8
        load1, _, _ = os.getloadavg()
        util_pct = round((load1 / _cached_cores) * 100, 1)
        health["cpu_usage_percent"] = util_pct
        health["cpu"] = {
            "cores": _cached_cores,
            "estimated_utilization": f"{min(100.0, util_pct)}%"
        }
    except Exception:
        health["cpu_usage_percent"] = 25.0
        health["cpu"] = {"cores": 8, "estimated_utilization": "25%"}

    # 3. Memory
    try:
        if not _cached_total_mem:
            mem_res = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=1)
            _cached_total_mem = round(int(mem_res.stdout.strip()) / (1024**3), 2)
        
        vm_res = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=1)
        vm_lines = vm_res.stdout
        free_pages = int(re.search(r"Pages free:\s+(\d+)", vm_lines).group(1)) if "Pages free:" in vm_lines else 0
        spec_pages = int(re.search(r"Pages speculative:\s+(\d+)", vm_lines).group(1)) if "Pages speculative:" in vm_lines else 0
        free_gb = round(((free_pages + spec_pages) * 4096) / (1024**3), 2)
        used_gb = round(max(0, _cached_total_mem - free_gb), 2)
        health["memory"] = {
            "total_gb": _cached_total_mem,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "used_percent": f"{round((used_gb / _cached_total_mem) * 100, 1)}%"
        }
    except Exception:
        health["memory"] = {"total_gb": 8.0, "used_percent": "75%"}

    # 4. Disk
    try:
        disk = shutil.disk_usage("/")
        health["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_percent": f"{round((disk.used / disk.total) * 100, 1)}%"
        }
    except Exception:
        health["disk"] = {"free_gb": 50.0, "used_percent": "70%"}

    _last_health = health
    _last_health_time = now
    return health

def get_mac_volume() -> int:
    try:
        res = subprocess.run(["osascript", "-e", "output volume of (get volume settings)"], capture_output=True, text=True, timeout=1)
        val = res.stdout.strip()
        return int(val) if val.isdigit() else 50
    except Exception:
        return 50

def set_mac_volume(level: int):
    try:
        level = max(0, min(100, int(level)))
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        return {"status": "success", "message": f"Master volume set to {level}%", "detail": f"Master volume adjusted to {level}%, Sir."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def open_mac_application(app_name: str):
    try:
        subprocess.run(["open", "-a", app_name], check=True)
        return {"status": "success", "message": f"Launched {app_name} successfully.", "detail": f"Opening {app_name} now, Sir."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to launch {app_name}: {str(e)}"}

_beacon_running = False
_beacon_thread = None

def start_sound_beacon():
    global _beacon_running, _beacon_thread
    if _beacon_running:
        return {"status": "already_running", "detail": "Beacon already sounding, Sir."}
    
    _beacon_running = True
    
    def _beacon_loop():
        # Unmute and set master volume to 100%
        set_mac_volume(100)
        try:
            subprocess.run(["osascript", "-e", "set volume without output muted"], check=False)
        except Exception:
            pass

        start_time = time.time()
        # Sound alert for up to 60 seconds or until stopped
        while _beacon_running and (time.time() - start_time < 60):
            for _ in range(2):
                if not _beacon_running:
                    break
                subprocess.run(["afplay", "/System/Library/Sounds/Submarine.aiff"], check=False)
                time.sleep(0.25)
            
            if not _beacon_running:
                break
            
            subprocess.run(["say", "-v", "Daniel", "[[volm 1.0]] Workstation location beacon active. Sir, I am right here."], check=False)
            time.sleep(1.0)
            
        stop_sound_beacon()

    _beacon_thread = threading.Thread(target=_beacon_loop, daemon=True)
    _beacon_thread.start()
    return {"status": "success", "detail": "Workstation sound beacon activated at 100% volume, Sir."}

def stop_sound_beacon():
    global _beacon_running
    _beacon_running = False
    return {"status": "success", "detail": "Location beacon disengaged, Sir."}

def control_mac_settings(action: str, value: str = "") -> dict:
    """
    Controls hardware and system settings on macOS:
    action: "lock", "sleep_display", "dark_mode_toggle", "dark_mode_on", "dark_mode_off", "empty_trash", "take_screenshot"
    """
    act = action.lower().strip()
    try:
        if act == "lock":
            # Native macOS lock screen via login framework (requires no accessibility keystroke permissions)
            try:
                import ctypes
                lib = ctypes.cdll.LoadLibrary('/System/Library/PrivateFrameworks/login.framework/login')
                lib.SACLockScreenImmediate()
                return {"status": "success", "detail": "Mac workstation locked down, Sir."}
            except Exception:
                pass
            # Fallback: display sleep
            try:
                subprocess.run(["pmset", "displaysleepnow"], check=False)
                return {"status": "success", "detail": "Display put to sleep, Sir."}
            except Exception:
                pass
            return {"status": "error", "message": "Could not lock workstation."}
            
        elif act in ["dark_mode_toggle", "dark_mode"]:
            subprocess.run(["osascript", "-e", "tell application \"System Events\" to tell appearance preferences to set dark mode to not dark mode"], check=True)
            return {"status": "success", "detail": "System appearance toggled, Sir."}
            
        elif act in ["dark_mode_on", "dark"]:
            subprocess.run(["osascript", "-e", "tell application \"System Events\" to tell appearance preferences to set dark mode to true"], check=True)
            return {"status": "success", "detail": "Dark mode enabled, Sir."}
            
        elif act in ["dark_mode_off", "light"]:
            subprocess.run(["osascript", "-e", "tell application \"System Events\" to tell appearance preferences to set dark mode to false"], check=True)
            return {"status": "success", "detail": "Light mode enabled, Sir."}
            
        elif act == "empty_trash":
            subprocess.run(["osascript", "-e", "tell application \"Finder\" to empty trash without warnings"], check=False)
            return {"status": "success", "detail": "Trash emptied, Sir."}
            
        elif act == "sleep_display":
            subprocess.run(["pmset", "displaysleepnow"], check=False)
            return {"status": "success", "detail": "Display put to sleep, Sir."}
            
        elif act in ["beacon", "find_mac", "find_my_mac", "sound_beacon"]:
            return start_sound_beacon()

        elif act in ["stop_beacon", "stop_alarm", "cancel_beacon", "dismiss_beacon"]:
            return stop_sound_beacon()

        elif act == "take_screenshot":
            desktop_path = os.path.expanduser(f"~/Desktop/Screenshot_{int(time.time())}.png")
            subprocess.run(["screencapture", "-x", desktop_path], check=True)
            return {"status": "success", "file": desktop_path, "detail": "Screenshot saved to your Desktop, Sir."}
            
        else:
            return {"status": "error", "message": f"Action \x27{action}\x27 not recognized."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
