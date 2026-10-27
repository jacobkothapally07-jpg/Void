import os
import subprocess
import time
import threading
import base64
import json
import ssl
import urllib.request
from config import GEMINI_API_KEY

VISION_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.6-flash"
]

def _call_gemini_vision(prompt: str, img_b64: str, system_inst: str = "") -> str:
    """Robust fallback caller across available vision models."""
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}
            ]
        }]
    }
    if system_inst:
        payload["system_instruction"] = {"parts": [{"text": system_inst}]}

    for model_name in VISION_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "JARVIS/1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10, context=get_ssl_context()) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            if e.code in [404, 429, 503]:
                continue
        except Exception:
            continue
    raise RuntimeError("All vision endpoints are temporarily unavailable.")

_watch_screen_active = False
_watch_thread = None
_LIVE_SCREEN_PATH = "/tmp/jarvis_live_screen.jpg"


def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def capture_screen_optimized(target_path: str = _LIVE_SCREEN_PATH) -> bool:
    """Takes a lightweight screen capture using macOS screencapture + sips."""
    try:
        subprocess.run(["screencapture", "-x", "-m", target_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sips", "-Z", "1280", "-s", "formatOptions", "60", target_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(target_path) and os.path.getsize(target_path) > 500
    except Exception:
        return False

def _watch_loop():
    global _watch_screen_active
    while _watch_screen_active:
        capture_screen_optimized(_LIVE_SCREEN_PATH)
        time.sleep(2.5)

def toggle_watch_screen(active: bool = True) -> dict:
    """
    Toggles continuous 'Watch My Screen' active monitoring mode.
    When active, Jarvis continuously caches the live screen in the background for zero-latency answers.
    """
    global _watch_screen_active, _watch_thread
    _watch_screen_active = active
    if active:
        if _watch_thread is None or not _watch_thread.is_alive():
            capture_screen_optimized(_LIVE_SCREEN_PATH)
            _watch_thread = threading.Thread(target=_watch_loop, daemon=True)
            _watch_thread.start()
        return {
            "status": "success",
            "active": True,
            "detail": "Watch My Screen mode is now active, Sir. I am keeping a continuous eye on your display."
        }
    else:
        return {
            "status": "success",
            "active": False,
            "detail": "Watch My Screen mode has been deactivated, Sir."
        }

def get_watch_screen_status() -> bool:
    return _watch_screen_active

def ask_about_screen(query: str = "Explain what is visible on my screen.") -> dict:
    """
    Analyzes whatever is currently displayed on screen and answers questions, debugs errors, or explains UI elements.
    """
    capture_screen_optimized(_LIVE_SCREEN_PATH)
    if not os.path.exists(_LIVE_SCREEN_PATH):
        return {"status": "error", "message": "Failed to capture Mac display."}
        
    try:
        with open(_LIVE_SCREEN_PATH, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        system_instruction = (
            "You are J.A.R.V.I.S., analyzing the user's live Mac display. "
            "Be razor-sharp, helpful, and concise (1-2 sentences). "
            "If debugging an error, explain the cause and exact fix directly."
        )
        answer = _call_gemini_vision(query, img_b64, system_instruction)
        return {"status": "success", "answer": answer, "detail": answer}
    except Exception as e:
        return {"status": "error", "message": f"Screen analysis failed: {str(e)}"}

def solve_and_paste_code(auto_paste: bool = True, language: str = "auto") -> dict:
    """
    Scans the screen for coding questions (LeetCode, HackerRank, IDE, exams),
    generates the optimal solution, copies to clipboard, and optionally auto-pastes via Cmd+V into the active editor.
    """
    capture_screen_optimized(_LIVE_SCREEN_PATH)
    if not os.path.exists(_LIVE_SCREEN_PATH):
        return {"status": "error", "message": "Could not capture display."}
        
    try:
        with open(_LIVE_SCREEN_PATH, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        prompt = (
            "You are an elite competitive programmer and AI operating assistant. "
            "Analyze this screenshot showing a programming problem or coding editor. "
            "1. Identify the problem description, inputs, outputs, and constraints. "
            "2. Identify the programming language chosen in the editor (or Python3 if unspecified). "
            "3. Provide ONLY the complete, optimal, bug-free code solution ready to be submitted or compiled. "
            "Do NOT include conversational markdown explanations or chit-chat. Just provide the code."
        )
        raw_code = _call_gemini_vision(prompt, img_b64)
            
        # Clean markdown code blocks if model wrapped it
        clean_code = raw_code.strip()
        if clean_code.startswith("```"):
            lines = clean_code.split("\n")
            if len(lines) > 2:
                # Remove first line (e.g. ```python) and last line (```)
                clean_code = "\n".join(lines[1:-1]).strip()

        # 1. Copy to macOS system clipboard
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(clean_code.encode("utf-8"))
        
        pasted = False
        target_name = "editor"
        if auto_paste:
            # 2. Switch focus to the user's active editor/browser and simulate Cmd+V
            paste_script = '''
            tell application "System Events"
                set appList to every application process whose visible is true and name is not "JarvisWidget" and name is not "Python" and name is not "Finder"
                if (count of appList) > 0 then
                    set targetApp to first item of appList
                    set frontmost of targetApp to true
                    set appName to name of targetApp
                    delay 0.35
                    keystroke "v" using command down
                    return appName
                end if
                return "Unknown"
            end tell
            '''
            res = subprocess.run(["osascript", "-e", paste_script], capture_output=True, text=True)
            if res.returncode == 0:
                pasted = True
                out = res.stdout.strip()
                if out:
                    target_name = out

        detail_msg = f"Problem solved. Code copied to clipboard and pasted directly into {target_name}, Sir." if pasted else "Problem solved and copied to clipboard, Sir."
        return {
            "status": "success",
            "pasted": pasted,
            "target": target_name,
            "code_preview": clean_code[:120] + "...",
            "detail": detail_msg
        }
    except Exception as e:
        return {"status": "error", "message": f"Coding solver encountered an error: {str(e)}"}
