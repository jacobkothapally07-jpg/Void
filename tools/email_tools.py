import subprocess
import urllib.parse

def get_unread_emails() -> dict:
    applescript = """tell application \"Mail\"
    set unreadList to (every message of inbox whose read status is false)
    set output to \"\"
    set countLimit to 5
    set i to 0
    repeat with msg in unreadList
        if i >= countLimit then exit repeat
        set output to output & \"From: \" & (sender of msg) & \" | Subject: \" & (subject of msg) & \"; \"
        set i to i + 1
    end repeat
    return output
end tell"""
    try:
        res = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
        mails = res.stdout.strip()
        if not mails:
            return {
                "status": "success",
                "unread_count": 0,
                "detail": "Your inbox is completely clear, Sir. No unread messages pending."
            }
        return {
            "status": "success",
            "unread_emails": mails,
            "detail": f"You have unread correspondence, Sir: {mails}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to access Apple Mail: {str(e)}"}

def draft_email_reply(recipient: str, subject: str, body: str) -> dict:
    clean_rec = recipient.strip()
    clean_sub = urllib.parse.quote(subject.strip())
    clean_body = urllib.parse.quote(body.strip())
    mailto_url = f"mailto:{clean_rec}?subject={clean_sub}&body={clean_body}"
    try:
        subprocess.run(["open", mailto_url], check=False)
        return {
            "status": "success",
            "recipient": clean_rec,
            "subject": subject,
            "detail": f"Drafted email to {clean_rec} with subject {subject}, Sir."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
