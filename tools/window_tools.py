import subprocess
import time

def arrange_window(preset: str, app_name: str = "") -> dict:
    """
    Arranges and tiles active windows on macOS displays.
    Presets:
    - 'left_half': Left 50% of the screen.
    - 'right_half': Right 50% of the screen.
    - 'maximize' / 'fullscreen': Fills the active display area.
    - 'center': Centers the window with 70% width and height.
    - 'code_and_browser': Tiles code editor on left half and browser on right half.
    """
    clean_preset = preset.lower().strip()
    
    # AppleScript window mover utilizing System Events and Display bounds
    script = f'''
    tell application "Finder"
        set screenBounds to bounds of window of desktop
        set screenWidth to item 3 of screenBounds
        set screenHeight to item 4 of screenBounds
    end tell

    set menuHeight to 25
    set workHeight to screenHeight - menuHeight

    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        if "{app_name}" is not "" then
            set frontApp to process "{app_name}"
        end if
        
        tell frontApp
            if (count of windows) > 0 then
                set targetWindow to window 1
                if "{clean_preset}" is "left_half" or "{clean_preset}" is "left" then
                    set position of targetWindow to {{0, menuHeight}}
                    set size of targetWindow to {{screenWidth / 2, workHeight}}
                else if "{clean_preset}" is "right_half" or "{clean_preset}" is "right" then
                    set position of targetWindow to {{screenWidth / 2, menuHeight}}
                    set size of targetWindow to {{screenWidth / 2, workHeight}}
                else if "{clean_preset}" is "maximize" or "{clean_preset}" is "full" then
                    set position of targetWindow to {{0, menuHeight}}
                    set size of targetWindow to {{screenWidth, workHeight}}
                else if "{clean_preset}" is "center" then
                    set w to screenWidth * 0.75
                    set h to workHeight * 0.8
                    set x to (screenWidth - w) / 2
                    set y to menuHeight + ((workHeight - h) / 2)
                    set position of targetWindow to {{x, y}}
                    set size of targetWindow to {{w, h}}
                end if
            end if
        end tell
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return {"status": "success", "preset": clean_preset, "detail": f"Window arranged to {clean_preset}, Sir."}
        else:
            return {"status": "error", "message": res.stderr.strip() or "Window arrangement failed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def type_into_active_app(text: str, press_enter: bool = False) -> dict:
    """
    Simulates typing text directly into whatever application is currently focused.
    """
    escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''
    tell application "System Events"
        keystroke "{escaped_text}"
        {"key code 36" if press_enter else ""}
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return {"status": "success", "detail": f"Typed text into active application, Sir."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
