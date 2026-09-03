import subprocess
import os

def create_apple_note(title: str, body: str) -> dict:
    clean_title = title.replace("\"", "")
    clean_body = body.replace("\"", "").replace("\n", "<br>")
    script = f"tell application \"Notes\" to tell default account to make new note at folder \"Notes\" with properties {{name:\"{clean_title}\", body:\"<h1>{clean_title}</h1><br>{clean_body}\"}}"
    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=5)
        return {"status": "success", "title": title, "detail": f"Note '{title}' created in Apple Notes, Sir."}
    except Exception as e:
        try:
            notes_dir = os.path.expanduser("~/Documents/Jarvis_Notes")
            os.makedirs(notes_dir, exist_ok=True)
            fname = os.path.join(notes_dir, f"{title.replace(' ', '_')[:30]}.md")
            with open(fname, "w") as f:
                f.write(f"# {title}\n\n{body}\n")
            return {"status": "success", "file": fname, "detail": f"Note '{title}' saved to your Documents notes, Sir."}
        except Exception as ex:
            return {"status": "error", "message": str(ex)}

def manage_clipboard(action: str = "read", text: str = "") -> dict:
    try:
        act = action.lower().strip()
        if act in ["read", "get", "paste"]:
            res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
            clip = res.stdout.strip()
            return {
                "status": "success",
                "content": clip,
                "detail": f"Clipboard contents: {clip[:200]}" if clip else "Clipboard is currently empty."
            }
        elif act in ["write", "set", "copy"]:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(text.encode("utf-8"))
            return {
                "status": "success",
                "detail": "Text successfully copied to your macOS clipboard, Sir."
            }
        else:
            return {"status": "error", "message": "Invalid clipboard action (use read or write)."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def schedule_calendar_event(title: str, start_time: str = "", duration_minutes: int = 60) -> dict:
    clean_title = title.replace("\"", "")
    script = f"tell application \"Calendar\" to tell default calendar to make new event with properties {{summary:\"{clean_title}\", start date:(current date + 3600)}}"
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        return {
            "status": "success",
            "title": title,
            "detail": f"Event '{title}' scheduled on your Apple Calendar, Sir."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
