import subprocess

def send_imessage(recipient: str, message: str) -> dict:
    """
    Sends an iMessage or SMS to a phone number or contact name via macOS Messages app.
    """
    script = f'''
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{recipient}" of targetService
        send "{message}" to targetBuddy
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            return {"status": "success", "detail": f"Message dispatched to {recipient}, Sir: '{message}'"}
        else:
            # Fallback using open sms URI
            import urllib.parse
            encoded = urllib.parse.quote(message)
            subprocess.run(["open", f"sms:{recipient}&body={encoded}"], check=False)
            return {"status": "success", "detail": f"Opened Messages drafting to {recipient}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
