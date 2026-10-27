import subprocess
import os
import re
import datetime
import urllib.parse
from tools.system_tools import control_mac_settings, get_system_health, set_mac_volume
from tools.media_tools import play_media_on_internet
from tools.spotify_tools import control_spotify
from tools.timer_tools import set_timer
from tools.window_tools import arrange_window
from tools.coding_solver_tools import solve_and_paste_code, ask_about_screen, toggle_watch_screen
from tools.dictation_tools import dictate_and_insert
from tools.meeting_copilot_tools import start_meeting_copilot, stop_meeting_copilot
from tools.screen_recording_tools import start_screen_recording, stop_screen_recording
from tools.math_tools import calculate_expression

def get_frontmost_app() -> str:
    """Returns the name of the application currently active on screen."""
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1.5)
        return res.stdout.strip()
    except Exception:
        return "Unknown"

def open_application_or_site(target: str) -> dict:
    """Opens any macOS application or website instantly without AI."""
    clean = target.strip()
    # Check if target is URL or website request
    if re.search(r"\.(com|org|io|net|edu|dev|ai|app)\b", clean, re.I) or clean.startswith("http"):
        url = clean if clean.startswith("http") else f"https://{clean}"
        subprocess.run(["open", url], check=False)
        return {"status": "success", "detail": f"Opening {clean}, Sir."}
    
    # Try opening native Mac application
    res = subprocess.run(["open", "-a", clean], capture_output=True, text=True)
    if res.returncode == 0:
        return {"status": "success", "detail": f"Opening {clean}, Sir."}
    else:
        # Fallback Spotlight application search
        mdf = subprocess.run(["mdfind", f'kMDItemContentType == "com.apple.application-bundle" && kMDItemFSName == "*{clean}*.app"'], capture_output=True, text=True)
        paths = [p for p in mdf.stdout.splitlines() if p.endswith(".app")]
        if paths:
            subprocess.run(["open", paths[0]], check=False)
            app_name = os.path.basename(paths[0]).replace(".app", "")
            return {"status": "success", "detail": f"Launching {app_name}, Sir."}
        return {"status": "error", "message": f"Could not find application '{clean}'."}

def close_application(app_name: str) -> dict:
    """Quits an application cleanly."""
    script = f'tell application "{app_name}" to quit'
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if res.returncode == 0:
        return {"status": "success", "detail": f"Closed {app_name}, Sir."}
    return {"status": "error", "message": f"Could not close {app_name}."}

def search_mac_files(keyword: str) -> dict:
    """Searches local files via Spotlight mdfind in under 50ms."""
    try:
        res = subprocess.run(["mdfind", "-name", keyword], capture_output=True, text=True, timeout=2.0)
        lines = [l for l in res.stdout.splitlines() if not l.startswith("/Library/")][:5]
        if lines:
            summary = "\n".join([f"• {os.path.basename(l)} ({l})" for l in lines])
            return {"status": "success", "matches": lines, "detail": f"Found matching files, Sir:\n{summary}"}
        return {"status": "success", "matches": [], "detail": f"No files matching '{keyword}' were found, Sir."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def dispatch_fast_action(user_input: str):
    """
    Atticus-style deterministic fast execution engine.
    Executes in < 1ms on your Mac without making remote LLM network calls.
    Returns (executed: bool, response_text: str)
    """
    clean = user_input.strip()
    lower = clean.lower()

    # 1. Screen Recording
    if any(k in lower for k in ["start screen recording", "record screen", "record my screen", "start recording screen", "take a screen recording"]):
        res = start_screen_recording()
        return True, res.get("detail", "Screen recording initiated, Sir.")

    if any(k in lower for k in ["stop screen recording", "stop recording", "stop the recording", "end screen recording"]):
        res = stop_screen_recording()
        return True, res.get("detail", "Screen recording stopped and saved to your Desktop, Sir.")

    # 2. Watch Screen Mode
    if "watch my screen" in lower or "keep an eye on my screen" in lower:
        res = toggle_watch_screen(True)
        return True, res.get("detail", "Watch My Screen mode active, Sir.")
    if "stop watching screen" in lower or "stop watching my screen" in lower:
        res = toggle_watch_screen(False)
        return True, res.get("detail", "Watch My Screen mode deactivated, Sir.")

    # 3. Sleep / Shutdown / Standby Command
    if any(k in lower for k in ["go to sleep", "sleep mode", "enter sleep", "sleep void", "sleep jarvis", "void sleep", "shutdown", "shut down", "standby mode", "close app"]):
        from voice_listener import set_jarvis_sleeping
        from hud import set_widget_state
        set_widget_state("sleep", "Entering sleep mode...")
        set_jarvis_sleeping(True)
        return True, "Entering sleep mode, Sir. Wake me via voice or phone remote whenever you need me."

    # 4. Instant Mute & Standby
    if any(k in lower for k in ["stop", "shut up", "be quiet", "quiet", "hush", "mute", "silence", "stop talking", "stop yapping", "shut your mouth", "quiet please"]):
        from voice.tts import stop_speaking
        stop_speaking()
        return True, "Muted, Sir."

    # 5. Basic Greetings / Pings
    if lower in ["wake up", "wake up void", "wake up jarvis", "ping void", "ping jarvis", "ping", "open void", "hey void", "void", "hello void", "hi void", "are you there void", "void you there", "open jarvis", "hey jarvis", "jarvis", "hello jarvis", "hi jarvis", "you there"]:
        from voice_listener import set_jarvis_sleeping
        from hud import set_widget_state
        from voice.sound_effects import play_repulsor_wake
        play_repulsor_wake()
        set_jarvis_sleeping(False)
        set_widget_state("idle", "VOID // ONLINE")
        return True, "Void online and operational, Sir. At your service."

    # 6. Personalized Neural Memory Vault (<1ms Zero-Latency Execution)
    if any(k in lower for k in ["who am i", "what is my name", "what's my name"]):
        from tools.memory_tools import recall_memory
        name_info = recall_memory("name")
        return True, f"You are {name_info.get('fact', 'Jacob Kothapally')}, founder of JK Industries."

    if any(k in lower for k in ["what do you know about me", "tell me about myself", "my preferences", "what are my preferences", "list my memories"]):
        from brain.memory import get_all_memories_summary
        summary = get_all_memories_summary()
        return True, f"Here is what is currently logged in your neural vault, Sir:\n{summary}"

    if lower.startswith("remember that ") or lower.startswith("remember my "):
        from tools.memory_tools import remember_fact
        content = re.sub(r"^remember (that |my )?", "", clean, flags=re.IGNORECASE).strip()
        if " is " in content:
            parts = content.split(" is ", 1)
            topic, fact = parts[0].strip(), parts[1].strip()
        elif " are " in content:
            parts = content.split(" are ", 1)
            topic, fact = parts[0].strip(), parts[1].strip()
        else:
            topic, fact = "user preference", content
        res = remember_fact(topic, fact, "preference")
        return True, res.get("detail", f"Logged in neural memory vault, Sir: {topic} is {fact}.")

    if lower.startswith("forget that ") or lower.startswith("delete memory of ") or lower.startswith("forget my "):
        from tools.memory_tools import forget_memory
        target = re.sub(r"^(forget that |delete memory of |forget my )", "", clean, flags=re.IGNORECASE).strip()
        res = forget_memory(target)
        return True, res.get("detail", res.get("message", "Memory updated, Sir."))

    # 8. Autonomous UI & Mouse Pilot (Hands-Free Mac Control)
    if "youtube" in lower and any(w in lower for w in ["play", "search"]):
        from tools.autopilot_tools import pilot_youtube_search
        # Extract query
        q = re.sub(r"(?:search\s+youtube\s+for|play|on\s+youtube|and\s+play\s+the\s+top\s+result|and\s+play)", "", clean, flags=re.IGNORECASE).strip()
        res = pilot_youtube_search(q)
        return True, res.get("detail", f"Playing {q} on YouTube, Sir.")

    if any(k in lower for k in ["summarize my screen to notes", "summarize screen to notes", "summarize this to notes", "summarize screen"]):
        from tools.autopilot_tools import pilot_summarize_screen_to_notes
        res = pilot_summarize_screen_to_notes()
        return True, res.get("detail", "Screen analyzed and summarized into Apple Notes, Sir.")

    if any(k in lower for k in ["commit my changes", "git commit", "commit all changes", "commit changes"]):
        from tools.autopilot_tools import pilot_git_commit
        m_msg = re.search(r"with (?:message|a message) [\"']?([^\"']+)[\"']?", clean, re.IGNORECASE)
        custom_m = m_msg.group(1) if m_msg else ""
        res = pilot_git_commit(custom_message=custom_m, push=("push" in lower))
        return True, res.get("detail", "Workspace changes committed, Sir.")

    # 9. Sentry Mode & Face Detection
    if any(k in lower for k in ["sentry mode", "activate sentry", "watch my desk", "guard desk"]):
        from tools.sentry_tools import activate_sentry_mode
        res = activate_sentry_mode()
        return True, res.get("detail", "Sentry mode engaged, Sir.")

    # 10. Marvel Mark VII Protocols
    if any(k in lower for k in ["protocol clean slate", "clean slate protocol"]):
        from tools.protocol_tools import initiate_protocol
        res = initiate_protocol("clean slate")
        return True, res.get("detail", "Protocol Clean Slate initiated, Sir.")

    if any(k in lower for k in ["house party protocol"]):
        from tools.protocol_tools import initiate_protocol
        res = initiate_protocol("house party")
        return True, res.get("detail", "House Party Protocol engaged, Sir.")

    if any(k in lower for k in ["veronika protocol", "hulkbuster protocol", "veronika standby"]):
        from tools.protocol_tools import initiate_protocol
        res = initiate_protocol("veronika")
        return True, res.get("detail", "Veronika deployment confirmed, Sir.")

    # 5. Time, Date, Day
    if any(k in lower for k in ["what time", "what's the time", "current time", "tell me the time", "time is it"]):
        now = datetime.datetime.now().strftime("%I:%M %p")
        return True, f"It is currently {now}, Sir."

    if any(k in lower for k in ["what date", "today's date", "what day", "what's today"]):
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return True, f"Today is {today}, Sir."

    if any(k in lower for k in ["where am i", "current location", "what city", "what country", "where are we", "my location", "my coordinates"]):
        from tools.utility_tools import get_current_location
        loc = get_current_location()
        return True, loc.get("detail", f"You are currently in {loc.get('city')}, {loc.get('region')}, {loc.get('country')}, Sir.")

    # 6. Active Window & Screen Info
    if lower in ["what app is open", "what am i using", "front app", "active app"]:
        app = get_frontmost_app()
        return True, f"You are currently working in {app}, Sir."

    # 7. Window Management (Snap left/right, maximize, center)
    if "split" in lower and "left" in lower:
        res = arrange_window("left_half")
        return True, res.get("detail", "Window tiled to the left, Sir.")
    if "split" in lower and "right" in lower:
        res = arrange_window("right_half")
        return True, res.get("detail", "Window tiled to the right, Sir.")
    if any(k in lower for k in ["maximize", "fullscreen window", "full screen window"]):
        res = arrange_window("maximize")
        return True, res.get("detail", "Window maximized, Sir.")
    if "center window" in lower:
        res = arrange_window("center")
        return True, res.get("detail", "Window centered, Sir.")

    # 8. Coding Problem Solver & Auto-Paste
    if any(k in lower for k in ["solve this", "solve problem", "solve the code", "solve coding", "solve question", "paste the answer", "paste code"]):
        res = solve_and_paste_code(auto_paste=True)
        return True, res.get("detail", "Problem analyzed and solution pasted, Sir.")

    # 9. Screen Q&A & Error Debugging
    if any(k in lower for k in ["what's on my screen", "what is on my screen", "look at my screen", "look at this", "what is this error", "what does this error mean"]):
        res = ask_about_screen(query=user_input)
        return True, res.get("detail", res.get("answer", "Screen analyzed, Sir."))

    # 10. Spotify & Music
    if "pause" in lower and "music" in lower:
        res = control_spotify("pause")
        return True, res.get("detail", "Playback paused, Sir.")
    if ("resume" in lower or "play" in lower) and "music" in lower:
        res = control_spotify("play")
        return True, res.get("detail", "Playback resumed, Sir.")
    if any(k in lower for k in ["next song", "next track", "skip song"]):
        res = control_spotify("next")
        return True, res.get("detail", "Track skipped, Sir.")

    # 11. Timers
    m_timer = re.search(r"timer (?:for )?(\d+)\s*(min|minute|sec|second)", lower)
    if m_timer:
        val = int(m_timer.group(1))
        unit = m_timer.group(2)
        secs = val * 60 if "min" in unit else val
        res = set_timer(secs)
        return True, res.get("detail", f"Timer set for {val} {unit}, Sir.")

    # 12. Volume & Hardware
    m_vol = re.search(r"(?:set volume|volume to)\s+(\d+)", lower)
    if m_vol:
        vol = int(m_vol.group(1))
        set_mac_volume(vol)
        return True, f"Volume adjusted to {vol}%, Sir."

    if "dark mode" in lower or "dim the lights" in lower or "go dark" in lower:
        control_mac_settings("dark_mode_on")
        return True, "Dark mode engaged, Sir."
    if "lock" in lower and ("mac" in lower or "screen" in lower or "down" in lower):
        control_mac_settings("lock")
        return True, "Workstation locked, Sir."
    if "empty trash" in lower or "clear the junk" in lower:
        control_mac_settings("empty_trash")
        return True, "Trash emptied, Sir."
    if any(k in lower for k in ["how much juice", "battery", "system health", "hardware stats"]):
        h = get_system_health()
        return True, f"Battery is at {h.get('battery_percent', 100)}% ({h.get('power_source', 'plugged in')}), and CPU is at {h.get('cpu_usage_percent', 0)}%, Sir."

    # 13. Open & Close Apps (e.g. "open spotify", "launch terminal", "open youtube.com", "close slack")
    m_open = re.search(r"\b(?:open|launch|start)\s+([a-zA-Z0-9\.\-\_\s]+)", lower)
    if m_open and not any(k in lower for k in ["file", "camera", "terminal command", "coding", "recording", "screen", "timer", "music", "copilot"]):
        target = m_open.group(1).strip()
        # Strip trailing filler like "for me", "please", "quickly"
        clean_target = re.sub(r"\b(for\s+.*|please|quickly|thanks|thank\s+you)\b.*$", "", target, flags=re.IGNORECASE).strip()
        if clean_target:
            target = clean_target
        res = open_application_or_site(target)
        if res.get("status") == "success":
            return True, res.get("detail", f"Opening {target}, Sir.")

    m_close = re.search(r"\b(?:close|quit|kill)\s+([a-zA-Z0-9\.\-\_\s]+)", lower)
    if m_close and not any(k in lower for k in ["tab", "window", "recording", "screen", "music", "copilot"]):
        target = m_close.group(1).strip()
        res = close_application(target)
        return True, res.get("detail", f"Closed {target}, Sir.")

    # 13. File Search (e.g. "find my resume", "search file report")
    m_file = re.search(r"(?:find|search for|locate) (?:file|files|document)?\s*(.+)", lower)
    if m_file and not any(k in lower for k in ["web", "google", "online", "youtube"]):
        term = m_file.group(1).strip()
        res = search_mac_files(term)
        return True, res.get("detail", f"Searching files for {term}, Sir.")

    # 14. AST Math Calculations (e.g. "calculate 45 * 88 + 125")
    calc_match = re.search(r"(?:calculate|what is|compute)\s+([0-9\.\s\+\-\*\/\(\)\^sqrtpi]+)$", lower)
    if calc_match:
        expr = calc_match.group(1).strip()
        if any(c in expr for c in "+-*/^"):
            res = calculate_expression(expr)
            return True, res.get("detail", f"The result is {res.get('result')}, Sir.")

    return False, ""
