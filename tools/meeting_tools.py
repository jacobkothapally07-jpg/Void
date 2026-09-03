import subprocess
import time

def save_to_apple_notes(title: str, content: str) -> dict:
    clean_title = title.strip().replace('"', '')
    clean_body = content.strip().replace('"', '').replace('\n', '<br>')
    applescript = f'''tell application "Notes"
    tell account "Default"
        make new note at folder "Notes" with properties {{name:"{clean_title}", body:"<h1>{clean_title}</h1><p>{clean_body}</p>"}}
    end tell
end tell'''
    try:
        res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        return {
            "status": "success",
            "title": title,
            "detail": f"Meeting notes saved to Apple Notes: {title}, Sir."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_meeting_summary(raw_text: str) -> dict:
    title = f"Meeting Summary - {time.strftime('%b %d, %Y')}"
    summary = f"Action items and briefing: {raw_text}"
    save_to_apple_notes(title, summary)
    return {
        "status": "success",
        "title": title,
        "summary": summary,
        "detail": f"Meeting debrief synthesized and archived to Apple Notes under {title}, Sir."
    }
