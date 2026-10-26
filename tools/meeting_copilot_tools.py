import subprocess
import time
import os
import datetime
from config import GEMINI_API_KEY

_meeting_active = False
_meeting_notes_history = []

def start_meeting_copilot(meeting_title: str = "Live Meeting Sync") -> dict:
    """
    Starts Meeting Copilot to monitor discussions, generate real-time assistance, and record structured meeting minutes.
    """
    global _meeting_active, _meeting_notes_history
    _meeting_active = True
    _meeting_notes_history = []
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    return {
        "status": "success",
        "meeting_active": True,
        "detail": f"Meeting Copilot activated for '{meeting_title}' at {timestamp}. I will document key decisions and action items, Sir."
    }

def record_meeting_point(point: str) -> dict:
    """Records an item or note into the active meeting log."""
    global _meeting_notes_history
    _meeting_notes_history.append(point)
    return {"status": "success", "detail": f"Recorded: {point}"}

def create_meeting_note(title: str, content: str) -> dict:
    """Saves structured meeting minutes directly into Apple Notes."""
    now_str = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    note_body = f"<b>{title}</b><br><small>{now_str}</small><br><br>{content.replace(chr(10), '<br>')}"
    
    script = f'''
    tell application "Notes"
        if not (exists folder "Jarvis Meeting Notes") then
            make new folder with properties {{name:"Jarvis Meeting Notes"}}
        end if
        set targetFolder to folder "Jarvis Meeting Notes"
        make new note at targetFolder with properties {{body:"{note_body}"}}
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return {"status": "success", "detail": f"Meeting minutes saved to Apple Notes under 'Jarvis Meeting Notes', Sir."}
        else:
            return {"status": "error", "message": res.stderr.strip() or "Failed to write to Notes."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def stop_meeting_copilot(title: str = "Meeting Summary") -> dict:
    """Stops the meeting copilot, formats all recorded points, and exports to Apple Notes."""
    global _meeting_active, _meeting_notes_history
    _meeting_active = False
    
    if not _meeting_notes_history:
        summary_content = "• Meeting concluded without explicit action items."
    else:
        summary_content = "\n".join([f"• {p}" for p in _meeting_notes_history])
        
    res = create_meeting_note(title, summary_content)
    _meeting_notes_history = []
    return {
        "status": "success",
        "meeting_active": False,
        "detail": f"Meeting Copilot deactivated. {res.get('detail', '')}"
    }
