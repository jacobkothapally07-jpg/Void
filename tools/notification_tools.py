import subprocess
import json
import os
import urllib.request
import urllib.error
import ssl

def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def send_desktop_notification(title: str, message: str, subtitle: str = "J.A.R.V.I.S."):
    """
    Displays a native macOS banner notification.
    """
    try:
        clean_title = title.replace('"', '\\"')
        clean_msg = message.replace('"', '\\"')
        clean_sub = subtitle.replace('"', '\\"')
        script = f'display notification "{clean_msg}" with title "{clean_title}" subtitle "{clean_sub}"'
        subprocess.run(["osascript", "-e", script], check=True)
        return {"status": "success", "message": "Desktop notification displayed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_phone_notification(message: str, title: str = "JARVIS Alert", topic: str = None):
    """
    Sends an instant push notification to your phone (iOS / Android) via ntfy.sh.
    To receive notifications, install the free 'ntfy' app on your phone and subscribe to your topic.
    """
    try:
        from config import NTFY_TOPIC
        target_topic = topic or NTFY_TOPIC or "jarvis_user_updates"
        url = f"https://ntfy.sh/{target_topic}"
        
        req = urllib.request.Request(
            url,
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "default",
                "Tags": "robot,bell",
                "User-Agent": "JARVIS-Assistant/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5, context=get_ssl_context()) as response:
            if response.status == 200:
                return {
                    "status": "success",
                    "message": f"Push notification dispatched to phone topic: '{target_topic}'",
                    "instructions": f"Subscribe on phone: https://ntfy.sh/{target_topic}"
                }
            else:
                return {"status": "error", "message": f"Server returned HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
