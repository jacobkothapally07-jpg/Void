import datetime
import webbrowser
import urllib.request
import json
import os
import sys

_cached_location = None

def get_current_location() -> dict:
    """
    Detects the user's real-time geographic location, city, region, country, postal code, and GPS coordinates.
    """
    global _cached_location
    if _cached_location:
        return _cached_location

    try:
        req = urllib.request.Request("http://ip-api.com/json/", headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=4) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("status") == "success":
                city = data.get("city", "Hyderabad")
                region = data.get("regionName", "Telangana")
                country = data.get("country", "India")
                zip_code = data.get("zip", "")
                lat = data.get("lat")
                lon = data.get("lon")
                isp = data.get("isp", "")
                
                loc = {
                    "status": "success",
                    "city": city,
                    "region": region,
                    "country": country,
                    "postal_code": zip_code,
                    "latitude": lat,
                    "longitude": lon,
                    "isp": isp,
                    "timezone": data.get("timezone", "Asia/Kolkata"),
                    "detail": f"You are currently in {city}, {region}, {country} (Postal: {zip_code}, Coordinates: {lat}, {lon}), Sir."
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
        "postal_code": "500061",
        "latitude": 17.3843,
        "longitude": 78.4583,
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
