import os
import json
import urllib.request
import urllib.error
import ssl
import re
import random
from config import GEMINI_API_KEY, LLM_PROVIDER
from brain.persona import SYSTEM_PROMPT
from tools import TOOL_DEFINITIONS, TOOL_REGISTRY

def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

LOCAL_FAREWELLS = [
    "Powering down auxiliary listening, Sir. I will remain on standby. Have a pleasant day.",
    "Very well, Sir. Entering low-power standby mode. Tap the sphere or say \x27Wake up\x27 whenever you need me.",
    "Standing down, Boss. Always a pleasure.",
    "Auxiliary protocols suspended. Standing by, Sir."
]

LOCAL_GREETINGS = [
    "Yes, Sir? Online and at your service.",
    "Ready for your command, Boss.",
    "Always a pleasure, Sir. How may I be of service?",
    "Auxiliary systems listening. Go ahead, Sir.",
    "Right here, Sir. Standing by."
]

class JarvisBrain:
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.model_pool = [
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-flash-latest"
        ]

    def execute_tool(self, tool_name: str, tool_args: dict):
        """Executes a registered tool function and returns the JSON result."""
        if tool_name not in TOOL_REGISTRY:
            return {"status": "error", "message": f"Tool \x27{tool_name}\x27 not recognized."}
        func = TOOL_REGISTRY[tool_name]
        try:
            print(f"  \033[94m⚡ Executing tool: {tool_name}({tool_args})\033[0m")
            result = func(**tool_args)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _http_post(self, url: str, payload: dict) -> dict:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "JARVIS/1.0"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12, context=get_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))

    def try_instant_local(self, user_input: str):
        clean = user_input.strip().lower()

        # Instant 0ms mute
        if any(w in clean for w in ["stop", "shut up", "be quiet", "quiet", "hush", "mute", "silence", "stop talking", "jarvis stop"]):
            from voice.tts import stop_speaking
            stop_speaking()
            return "Muted, Sir."

        # Standalone wake/ping
        if clean in ["wake up", "wake up jarvis", "ping jarvis", "ping", "open jarvis", "hey jarvis", "jarvis"]:
            return random.choice(LOCAL_GREETINGS)

        if any(w in clean for w in ["goodbye", "bye jarvis", "bye", "standby mode", "go to sleep", "shut down", "stop listening", "that will be all"]):
            return random.choice(LOCAL_FAREWELLS)

        # FAST LOCAL INTENT ROUTING (0ms latency, 100% reliability, no API lag)
        # Instant Time & Date
        if any(k in clean for k in ["what time", "what's the time", "current time", "tell me the time", "time is it"]):
            import datetime
            now_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"It is currently {now_time}, Sir."

        if any(k in clean for k in ["what date", "today's date", "what day", "what's today"]):
            import datetime
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {today}, Sir."

        if any(k in clean for k in ["where am i", "current location", "what city"]):
            res = self.execute_tool("get_current_location", {})
            return res.get("detail", "You are currently in Hyderabad, India, Sir.")

        # Coding problem solve & auto-paste
        if any(k in clean for k in ["solve this", "solve problem", "solve the code", "solve coding", "solve question", "paste the answer", "paste code"]):
            res = self.execute_tool("solve_and_paste_code", {"auto_paste": True})
            return res.get("detail", "Problem analyzed and solution processed, Sir.")

        # Screen watch
        if "watch my screen" in clean or "keep an eye on my screen" in clean or "start watching screen" in clean:
            res = self.execute_tool("toggle_watch_screen", {"active": True})
            return res.get("detail", "Watch My Screen mode active, Sir.")
        if "stop watching screen" in clean or "stop watching my screen" in clean:
            res = self.execute_tool("toggle_watch_screen", {"active": False})
            return res.get("detail", "Watch My Screen mode deactivated, Sir.")

        # Screen Q&A / error detection
        if any(k in clean for k in ["what's on my screen", "what is on my screen", "look at my screen", "look at this", "what is this error", "what does this error mean"]):
            res = self.execute_tool("ask_about_screen", {"query": user_input})
            return res.get("detail", res.get("answer", "I have examined your screen, Sir."))

        # Window arrange
        if "split" in clean and "left" in clean:
            res = self.execute_tool("arrange_window", {"preset": "left_half"})
            return res.get("detail", "Window arranged to the left, Sir.")
        if "split" in clean and "right" in clean:
            res = self.execute_tool("arrange_window", {"preset": "right_half"})
            return res.get("detail", "Window arranged to the right, Sir.")
        if "maximize" in clean or "fullscreen" in clean:
            res = self.execute_tool("arrange_window", {"preset": "maximize"})
            return res.get("detail", "Window maximized, Sir.")
        if "center window" in clean:
            res = self.execute_tool("arrange_window", {"preset": "center"})
            return res.get("detail", "Window centered, Sir.")

        # Dictation
        if clean.startswith("dictate ") or clean.startswith("type this "):
            raw = re.sub(r"^(dictate|type this)\s+", "", user_input, flags=re.IGNORECASE)
            res = self.execute_tool("dictate_and_insert", {"raw_text": raw})
            return res.get("detail", f"Dictated: '{raw}'")

        # Meeting Copilot
        if "start meeting" in clean or "meeting notes" in clean or "meeting copilot" in clean:
            res = self.execute_tool("start_meeting_copilot", {"meeting_title": "Live Call"})
            return res.get("detail", "Meeting Copilot active. I am taking notes, Sir.")
        if "finish meeting" in clean or "save meeting" in clean or "end meeting" in clean:
            res = self.execute_tool("stop_meeting_copilot", {"title": "Meeting Summary"})
            return res.get("detail", "Meeting concluded and notes saved to Apple Notes, Sir.")

        # Spotify
        if "pause" in clean and "music" in clean:
            res = self.execute_tool("control_spotify", {"action": "pause"})
            return res.get("detail", "Spotify playback paused, Sir.")
        if ("resume" in clean or "play" in clean) and "music" in clean:
            res = self.execute_tool("control_spotify", {"action": "play"})
            return res.get("detail", "Spotify playback resumed, Sir.")
        if "next song" in clean or "next track" in clean or "skip song" in clean:
            res = self.execute_tool("control_spotify", {"action": "next"})
            return res.get("detail", "Track skipped, Sir.")

        # Timers
        m = re.search(r"timer (?:for )?(\d+)\s*(min|minute|sec|second)", clean)
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            secs = val * 60 if "min" in unit else val
            res = self.execute_tool("set_timer", {"duration_seconds": secs})
            return res.get("detail", f"Timer set for {val} {unit}, Sir.")

        # Mac Hardware & Settings
        if "dark mode" in clean or "dim the lights" in clean or "go dark" in clean:
            res = self.execute_tool("control_mac_settings", {"action": "dark_mode_on"})
            return res.get("detail", "Dark mode engaged, Sir.")
        if "lock" in clean and ("mac" in clean or "screen" in clean or "down" in clean):
            res = self.execute_tool("control_mac_settings", {"action": "lock"})
            return res.get("detail", "Screen locked, Sir.")
        if "empty trash" in clean or "clear the junk" in clean:
            res = self.execute_tool("control_mac_settings", {"action": "empty_trash"})
            return res.get("detail", "Trash emptied, Sir.")
        if "how much juice" in clean or "battery" in clean or "system health" in clean:
            res = self.execute_tool("get_system_health", {})
            return f"Battery is at {res.get('battery_percent', 100)}% ({res.get('power_source', 'plugged in')}), and CPU is stable at {res.get('cpu_usage_percent', 0)}%, Sir."

        # Math Calculations
        calc_match = re.search(r"(?:calculate|what is|compute)\s+([0-9\.\s\+\-\*\/\(\)\^sqrtpi]+)$", clean)
        if calc_match:
            expr = calc_match.group(1).strip()
            if any(c in expr for c in "+-*/^"):
                res = self.execute_tool("calculate_expression", {"expression": expr})
                return res.get("detail", f"The answer is {res.get('result')}, Sir.")

        return None

    def respond(self, user_input: str) -> str:
        clean = user_input.strip()
        if not clean:
            return "Standing by, Sir."

        # Keep last 12 message turns for coherent conversational memory
        if len(self.messages) > 13:
            self.messages = [self.messages[0]] + self.messages[-12:]
        local_ans = self.try_instant_local(clean)
        if local_ans:
            return local_ans

        if not GEMINI_API_KEY:
            return "My apologies, Sir, but GEMINI_API_KEY is currently unset."

        # Full native Gemini 3.1 intelligence with complete tool calling
        contents = []
        for msg in self.messages[1:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": clean}]})

        gemini_tools = [{
            "function_declarations": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"]
                } for t in TOOL_DEFINITIONS
            ]
        }]

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": contents,
            "tools": gemini_tools,
            "generationConfig": {"temperature": 0.4}
        }

        for model_name in self.model_pool:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            try:
                data = self._http_post(url, payload)
                if "candidates" not in data or len(data["candidates"]) == 0:
                    continue

                candidate = data["candidates"][0]
                parts = candidate.get("content", {}).get("parts", [])
                function_calls = [p["functionCall"] for p in parts if "functionCall" in p]
                
                if function_calls:
                    tool_parts = []
                    for fc in function_calls:
                        fname = fc["name"]
                        fargs = fc.get("args", {})
                        tool_output = self.execute_tool(fname, fargs)
                        tool_parts.append({
                            "functionResponse": {
                                "name": fname,
                                "response": {"name": fname, "content": tool_output}
                            }
                        })

                    model_turn = candidate["content"]
                    updated_contents = list(contents)
                    updated_contents.append(model_turn)
                    updated_contents.append({"role": "user", "parts": tool_parts})

                    follow_up_payload = {
                        "contents": updated_contents,
                        "tools": gemini_tools
                    }

                    follow_up_data = self._http_post(url, follow_up_payload)
                    final_parts = follow_up_data["candidates"][0]["content"].get("parts", [])
                    final_text = "".join([p.get("text", "") for p in final_parts if "text" in p])
                    
                    if not final_text:
                        for tp in tool_parts:
                            resp = tp.get("functionResponse", {}).get("response", {}).get("content", {})
                            if isinstance(resp, dict):
                                if "detail" in resp:
                                    final_text = resp["detail"]
                                    break
                                elif "message" in resp:
                                    final_text = resp["message"]
                                    break
                        if not final_text:
                            final_text = "Operation completed successfully, Sir."

                    self.messages.append({"role": "user", "content": clean})
                    self.messages.append({"role": "assistant", "content": final_text})
                    return final_text
                else:
                    text_response = "".join([p.get("text", "") for p in parts if "text" in p])
                    if not text_response:
                        continue
                    self.messages.append({"role": "user", "content": clean})
                    self.messages.append({"role": "assistant", "content": text_response})
                    return text_response

            except Exception:
                continue

        return "Right away, Sir. Processing your request."
