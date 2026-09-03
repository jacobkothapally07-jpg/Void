import subprocess
import urllib.parse
import re

def send_text_message(recipient: str, message: str) -> dict:
    clean_recipient = recipient.strip()
    clean_msg = message.strip()
    
    # Try sending via Messages app sms link
    try:
        encoded_body = urllib.parse.quote(clean_msg)
        sms_url = f"sms:{clean_recipient}&body={encoded_body}"
        subprocess.run(["open", sms_url], check=False)
        return {
            "status": "success",
            "recipient": clean_recipient,
            "message": clean_msg,
            "detail": f"Dispatched text message to {clean_recipient}."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to send text: {str(e)}"}

def make_phone_call(contact_or_number: str, is_facetime_video: bool = False) -> dict:
    target = contact_or_number.strip()
    clean_target = re.sub(r"[^0-9a-zA-Z+@.-]", "", target)
    scheme = "facetime" if is_facetime_video else "tel"
    call_url = f"{scheme}://{clean_target}"

    try:
        subprocess.run(["open", call_url], check=True)
        call_type = "FaceTime Video" if is_facetime_video else "Phone Call"
        return {
            "status": "success",
            "target": target,
            "type": call_type,
            "detail": f"Initiated {call_type} to {target}."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to place call: {str(e)}"}
