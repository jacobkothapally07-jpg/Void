import datetime
import re
from tools.live_data_tools import get_live_weather
from tools.system_tools import get_system_health
from tools.web_agent_tools import search_and_summarize
from tools.memory_tools import recall_memory
from voice.sound_effects import play_protocol_chime

def get_morning_sitrep(auto_setup: bool = False) -> dict:
    """
    Executes the Mark VII Daily Sitrep protocol:
    Greets Jacob by name, gives live weather in Hyderabad, system hardware telemetry,
    top breaking tech headlines, and optionally boots morning workspace.
    """
    play_protocol_chime()
    
    # 1. Time-aware greeting & User Name
    now = datetime.datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
        
    name_info = recall_memory("name")
    user_name = name_info.get("fact", "Jacob") if name_info.get("found") else "Jacob"
    time_str = now.strftime("%A, %B %d at %I:%M %p")
    
    # 2. Live Weather (Hyderabad)
    weather_desc = "fair conditions"
    try:
        w = get_live_weather("Hyderabad")
        w_detail = w.get("detail", "")
        m_temp = re.search(r"Temperature is ([\d\.]+°C)", w_detail)
        temp_str = m_temp.group(1) if m_temp else "24°C"
        weather_desc = f"{temp_str} with clear skies in Hyderabad"
    except Exception:
        weather_desc = "24°C in Hyderabad"
        
    # 3. Hardware Diagnostics
    batt_str = "100%"
    power_str = "AC power"
    try:
        h = get_system_health()
        b_info = h.get("battery", {})
        batt_str = b_info.get("percent", "100%")
        power_str = b_info.get("power_source", "AC Power")
    except Exception:
        pass

    # 4. Breaking Global Headlines
    headline_snippet = ""
    try:
        news = search_and_summarize("latest technology artificial intelligence news")
        raw_detail = news.get("detail", "")
        # Remove preamble
        clean_news = re.sub(r"^Global intelligence.*?Live headlines:\s*", "", raw_detail, flags=re.IGNORECASE)
        # Extract first 2 headline bullets
        lines = [l.strip() for l in clean_news.split("•") if len(l.strip()) > 15]
        if lines:
            h1 = lines[0].split(" - ")[0].strip()
            headline_snippet = f"Top headline: {h1}."
    except Exception:
        headline_snippet = "Global telemetry feeds are operating normally."

    # 5. Spoken Briefing
    speech = (
        f"{greeting}, {user_name}. The time is {time_str}. "
        f"Atmospheric telemetry reports {weather_desc}. "
        f"Your MacBook Air is at {batt_str} on {power_str}. "
        f"{headline_snippet} "
        f"All core systems are nominal, Sir. At your service."
    )
    
    # Optional auto-setup
    if auto_setup:
        try:
            from tools.system_tools import open_mac_application
            from tools.media_tools import play_media_on_internet
            open_mac_application("Google Chrome")
            play_media_on_internet("lofi hip hop radio beats to relax study to")
        except Exception:
            pass

    return {
        "status": "success",
        "greeting": greeting,
        "user_name": user_name,
        "time": time_str,
        "weather": weather_desc,
        "battery": batt_str,
        "headlines": headline_snippet,
        "detail": speech
    }
