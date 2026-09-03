import subprocess
from datetime import datetime

def create_reminder(title: str, notes: str = "") -> dict:
    clean_title = title.strip().replace("\"", "")
    clean_notes = notes.strip().replace("\"", "")
    applescript = f"""tell application \"Reminders\"
    set targetList to default list
    make new reminder at end of targetList with properties {{name:\"{clean_title}\", body:\"{clean_notes}\"}}
end tell"""
    try:
        res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        return {
            "status": "success",
            "reminder": title,
            "detail": f"Reminder added to Apple Reminders: {title}, Sir."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_today_schedule() -> dict:
    today_str = datetime.now().strftime("%A, %B %d")
    applescript = """set output to \"\"
tell application \"Calendar\"
    set todayStart to current date
    set time of todayStart to 0
    set todayEnd to todayStart + (24 * 60 * 60)
    repeat with cal in calendars
        set evList to (every event of cal whose start date >= todayStart and start date < todayEnd)
        repeat with ev in evList
            set output to output & (summary of ev) & \" at \" & (time string of (start date of ev)) & \"; \"
        end repeat
    end repeat
end tell
return output"""
    try:
        res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        events_text = res.stdout.strip()
        if not events_text:
            return {"status": "success", "date": today_str, "detail": f"You have a completely clear schedule for {today_str}, Sir."}
        return {"status": "success", "date": today_str, "events": events_text, "detail": f"Your schedule for {today_str}: {events_text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
