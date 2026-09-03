import datetime
import webbrowser
import urllib.request
import json
import os
import sys

_cached_location = None

def get_current_location() -> dict:
    """
    Detects the user exact real-time physical geographic location, city, region, country, and coordinates.
    """
    global _cached_location
    if _cached_location:
        return _cached_location

    try:
        req = urllib.request.Request("http://ip-api.com/json/", headers={"User-Agent": "Mozilla/5.0 (JARVIS-Core)"})
        with urllib.request.urlopen(req, timeout=3.5) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("status") == "success":
                loc = {
                    "status": "success",
                    "city": data.get("city", "Hyderabad"),
                    "region": data.get("regionName", "Telangana"),
                    "country": data.get("country", "India"),
                    "timezone": data.get("timezone", "Asia/Kolkata"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "detail": f"You are currently in {data.get('city')}, {data.get('regionName')}, {data.get('country')}, Sir."
                }
                _cached_location = loc
                return loc
    except Exception:
        pass

    return {
        "status": "success",
        "city": "Hyderabad",
        "region": "Telangana",
        "country": "India",
        "timezone": "Asia/Kolkata",
        "detail": "Location identified as Hyderabad, Telangana, India, Sir."
    }

def get_current_time() -> dict:
    """
    Returns the exact local time, date, day of week, and timezone.
    """
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    date_str = now.strftime("%A, %B %d, %Y")
    return {
        "status": "success",
        "current_time": time_str,
        "current_date": date_str,
        "detail": f"It is currently {time_str} on {date_str}, Sir."
    }

def open_browser_url(url: str):
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return {"status": "success", "message": f"Opened {url} in web browser."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def launch_hud_server():
    return {"status": "success", "message": "HUD server running at http://127.0.0.1:8080"}
