import subprocess
import urllib.parse

def control_spotify(action: str, query: str = "") -> dict:
    """
    Controls Spotify playback directly on macOS via AppleScript.
    Actions supported:
    - 'play': Resumes playback or plays a specific query.
    - 'pause': Pauses playback.
    - 'toggle': Toggles play/pause.
    - 'next': Skips to next track.
    - 'previous': Returns to previous track.
    - 'now_playing': Gets current song, artist, and album.
    - 'volume': Sets Spotify specific volume (0 to 100).
    """
    clean_action = action.lower().strip()
    
    if clean_action == "pause":
        cmd = 'tell application "Spotify" to pause'
    elif clean_action == "toggle":
        cmd = 'tell application "Spotify" to playpause'
    elif clean_action == "next":
        cmd = 'tell application "Spotify" to next track'
    elif clean_action == "previous":
        cmd = 'tell application "Spotify" to previous track'
    elif clean_action == "now_playing":
        script = '''
        if application "Spotify" is running then
            tell application "Spotify"
                set t_name to name of current track
                set a_name to artist of current track
                set alb_name to album of current track
                return t_name & " by " & a_name & " from " & alb_name
            end tell
        else
            return "Spotify is not running."
        end if
        '''
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return {"status": "success", "detail": res.stdout.strip()}
    elif clean_action == "play":
        if query:
            clean_q = query.strip()
            # Open Spotify search URI directly
            uri = f"spotify:search:{urllib.parse.quote(clean_q)}"
            subprocess.run(["open", uri], check=False)
            return {"status": "success", "detail": f"Searching and queuing '{clean_q}' on Spotify, Sir."}
        else:
            cmd = 'tell application "Spotify" to play'
    else:
        cmd = 'tell application "Spotify" to playpause'

    res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
    if res.returncode == 0:
        return {"status": "success", "detail": f"Spotify command '{clean_action}' executed successfully."}
    else:
        return {"status": "error", "message": res.stderr.strip() or "Could not control Spotify."}
