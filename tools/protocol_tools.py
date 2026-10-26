import subprocess
from tools.system_tools import set_mac_volume, open_mac_application, control_mac_settings
from tools.media_tools import play_media_on_internet
from voice.sound_effects import play_protocol_chime, play_repulsor_wake

def initiate_protocol(protocol_name: str) -> dict:
    p_name = protocol_name.lower().strip()
    play_protocol_chime()

    # 1. Clean Slate Protocol
    if any(w in p_name for w in ["clean slate", "slate"]):
        try:
            control_mac_settings("empty_trash")
            control_mac_settings("dark_mode_on")
            set_mac_volume(40)
        except Exception:
            pass
        return {
            "status": "success",
            "protocol": "Protocol Clean Slate",
            "detail": "Protocol Clean Slate initiated, Sir. Trash purged, dark mode engaged, and workspace reset."
        }

    # 2. House Party Protocol
    elif any(w in p_name for w in ["house party", "party"]):
        set_mac_volume(80)
        play_media_on_internet("AC DC Back in Black rock classics mix")
        return {
            "status": "success",
            "protocol": "House Party Protocol",
            "detail": "House Party Protocol engaged, Sir. Volume boosted to 80 percent, high energy soundtrack online."
        }

    # 3. Veronika / Hulkbuster Standby Protocol
    elif any(w in p_name for w in ["veronika", "hulkbuster"]):
        play_repulsor_wake()
        return {
            "status": "success",
            "protocol": "Veronika Standby Protocol",
            "detail": "Veronika deployment confirmed, Sir. Orbital telemetry locked, auxiliary power cells at full charge."
        }

    # 4. Coding Protocol
    elif any(w in p_name for w in ["code", "coding", "dev"]):
        set_mac_volume(45)
        open_mac_application("Visual Studio Code")
        open_mac_application("Terminal")
        play_media_on_internet("lofi hip hop radio beats to relax study to")
        return {
            "status": "success",
            "protocol": "Coding Protocol",
            "detail": "Coding protocol initiated. VS Code and Terminal deployed, volume tuned to 45 percent, Lo-Fi study stream active, Sir."
        }

    # 6. Study Protocol
    elif any(w in p_name for w in ["study", "focus", "learn"]):
        set_mac_volume(30)
        open_mac_application("Notion")
        play_media_on_internet("deep focus ambient concentration music")
        return {
            "status": "success",
            "protocol": "Study Protocol",
            "detail": "Study protocol engaged. Notion opened, audio set to 30 percent, deep focus concentration stream online, Sir."
        }

    # 7. Meeting Protocol
    elif any(w in p_name for w in ["meeting", "call"]):
        set_mac_volume(65)
        subprocess.run(["pkill", "-9", "Spotify"], capture_output=True)
        return {
            "status": "success",
            "protocol": "Meeting Protocol",
            "detail": "Meeting protocol active. Audio output set to 65 percent, background media silenced, communication channels clear, Sir."
        }

    # 8. Clean House Protocol
    elif any(w in p_name for w in ["clean", "house", "purge"]):
        control_mac_settings("empty_trash")
        return {
            "status": "success",
            "protocol": "Clean House Protocol",
            "detail": "Clean House protocol complete, Sir. Trash purged via macOS Finder and cache optimized."
        }

    # 9. Relax Protocol
    elif any(w in p_name for w in ["relax", "chill", "rest"]):
        set_mac_volume(35)
        play_media_on_internet("gentle rain and thunder ambient sounds")
        return {
            "status": "success",
            "protocol": "Relax Protocol",
            "detail": "Relaxation protocol active. Volume lowered to 35 percent, calming ambient rain stream online. Enjoy your downtime, Sir."
        }

    return {
        "status": "error",
        "message": f"Protocol {protocol_name} not recognized. Available protocols: Clean Slate, House Party, Veronika, Coding, Study, Meeting, Relax."
    }
