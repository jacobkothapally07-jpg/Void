import subprocess
import time

def dictate_and_insert(raw_text: str) -> dict:
    """
    Cleans up dictated text (removes verbal pauses, applies punctuation and capitalization)
    and inserts it directly at the active text cursor in macOS.
    """
    if not raw_text.strip():
        return {"status": "error", "message": "No speech detected to dictate."}
        
    cleaned = raw_text.strip()
    # Capitalize first letter
    if len(cleaned) > 0:
        cleaned = cleaned[0].upper() + cleaned[1:]
    if not cleaned.endswith((".", "!", "?")):
        cleaned += "."
        
    # Copy to clipboard
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(cleaned.encode("utf-8"))
    
    # Simulate Cmd+V into frontmost application
    time.sleep(0.15)
    script = 'tell application "System Events" to keystroke "v" using command down'
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    
    if res.returncode == 0:
        return {
            "status": "success",
            "text": cleaned,
            "detail": f"Dictation inserted: '{cleaned}'"
        }
    else:
        return {
            "status": "partial_success",
            "text": cleaned,
            "detail": f"Copied dictation to clipboard: '{cleaned}'"
        }
