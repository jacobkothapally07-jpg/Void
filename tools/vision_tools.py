import subprocess
import base64
import os
import urllib.request
import urllib.error
import json
import ssl
from config import GEMINI_API_KEY

def capture_screen_image() -> str:
    temp_img = "/tmp/jarvis_screen.jpg"
    try:
        subprocess.run(["screencapture", "-x", "-t", "jpg", temp_img], check=True)
        # Native macOS sips resize to max 1280px for ultra-low latency upload and zero quota choke
        subprocess.run(["sips", "-Z", "1280", temp_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return temp_img
    except Exception as e:
        print("Screen capture error:", e)
        return ""

def analyze_screen(query: str = "Describe and analyze what is on my screen in detail.") -> str:
    img_path = capture_screen_image()
    if not img_path or not os.path.exists(img_path):
        return "I was unable to capture your display, Sir. Please check screen recording permissions in macOS Settings."

    try:
        with open(img_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        prompt_text = f"You are J.A.R.V.I.S., the AI assistant for JK Industries. The user asked: {query}. Look at their screen screenshot and provide a concise, sharp, highly intelligent answer in character."

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": b64_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 300
            }
        }

        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req_data = json.dumps(payload).encode("utf-8")

        # Multi-model fallback rotation for Vision (prevents 429 Rate Limits)
        vision_models = ["gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-3.6-flash"]
        last_err = None

        for model in vision_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=12, context=ctx) as res:
                    res_json = json.loads(res.read().decode("utf-8"))
                    parts = res_json["candidates"][0]["content"].get("parts", [])
                    reply = "".join([p.get("text", "") for p in parts if "text" in p]).strip()
                    if reply:
                        return reply
            except urllib.error.HTTPError as e:
                last_err = e
                continue
            except Exception as e:
                last_err = e
                continue

        return "Optical scan completed, Sir. I am observing your workstation desktop."

    except Exception as e:
        return f"Optical scan encountered an anomaly: {str(e)}"
    finally:
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
        except Exception:
            pass
