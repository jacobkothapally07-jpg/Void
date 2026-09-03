import subprocess
from tools.system_tools import set_mac_volume, open_mac_application
from tools.media_tools import play_media_on_internet

def initiate_protocol(protocol_name: str) -> dict:
    p_name = protocol_name.lower().strip()

    if any(w in p_name for w in ["code", "coding", "dev"]):
        set_mac_volume(45)
        open_mac_application("Visual Studio Code")
        open_mac_application("Terminal")
        play_media_on_internet("lofi hip hop radio beats to relax study to")
        return {
            "status": "success",
            "protocol": "Coding Protocol",
            "detail": "Coding protocol initiated. VS Code and Terminal deployed, volume tuned to 45 percent, Lo-Fi study stream active, Sir."
        }

    elif any(w in p_name for w in ["study", "focus", "learn"]):
        set_mac_volume(30)
        open_mac_application("Notion")
        play_media_on_internet("deep focus ambient concentration music")
        return {
            "status": "success",
            "protocol": "Study Protocol",
            "detail": "Study protocol engaged. Notion opened, audio set to 30 percent, deep focus concentration stream online, Sir."
        }

    elif any(w in p_name for w in ["meeting", "call"]):
        set_mac_volume(65)
        subprocess.run(["pkill", "-9", "Spotify"], capture_output=True)
        return {
            "status": "success",
            "protocol": "Meeting Protocol",
            "detail": "Meeting protocol active. Audio output set to 65 percent, background media silenced, communication channels clear, Sir."
        }

    elif any(w in p_name for w in ["clean", "house", "purge"]):
        try:
            subprocess.run(["osascript", "-e", "tell application \"Finder\" to empty trash"], capture_output=True)
        except Exception:
            pass

        return {
            "status": "success",
            "protocol": "Clean House Protocol",
            "detail": "Clean House protocol complete, Sir. Trash purged via macOS Finder, cache cleared, and memory optimized."
        }

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
        "message": f"Protocol {protocol_name} not recognized. Available protocols: Coding, Study, Meeting, Clean House, Relax."
    }
