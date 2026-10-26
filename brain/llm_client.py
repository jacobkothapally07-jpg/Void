import os
import json
import urllib.request
import urllib.error
import ssl
import re
import random
from config import GEMINI_API_KEY, LLM_PROVIDER
from brain.persona import get_system_prompt
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
            {"role": "system", "content": get_system_prompt()}
        ]
        self.model_pool = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite"
        ]

    def _call_local_ollama(self, prompt: str) -> str:
        """Runs offline on M3 Apple Silicon GPU/Neural Engine via Ollama (llama3.2:1b)."""
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:1b",
            "system": "You are J.A.R.V.I.S., Tony Stark's witty, polite AI assistant. Speak like Paul Bettany in 1-2 crisp, intelligent sentences. Address the user as Sir.",
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 60, "temperature": 0.5}
        }
        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                ans = data.get("response", "").strip()
                if ans:
                    return ans
        except Exception as e:
            print(f"[Ollama Fallback Notice] {e}")
        return None

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

        # FAST DETERMINISTIC ATTICUS ENGINE (0ms, 100% reliable, zero cloud lag)
        from brain.fast_engine import dispatch_fast_action
        matched, fast_reply = dispatch_fast_action(clean)
        if matched and fast_reply:
            return fast_reply

        # Standalone wake/ping
        if clean in ["wake up", "wake up jarvis", "ping jarvis", "ping", "open jarvis", "hey jarvis", "jarvis"]:
            return random.choice(LOCAL_GREETINGS)

        if any(w in clean for w in ["goodbye", "bye jarvis", "bye", "standby mode", "go to sleep", "shut down", "stop listening", "that will be all"]):
            from voice_listener import set_jarvis_sleeping
            from hud import set_widget_state
            set_widget_state("sleep", "Entering sleep mode...")
            set_jarvis_sleeping(True)
            return "Entering sleep mode, Sir. Wake me via shortcut or menu icon whenever you need me."

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
            "system_instruction": {"parts": [{"text": get_system_prompt()}]},
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

        # Fallback to local on-device Ollama LLM (M3 Neural Engine, 0ms network latency)
        local_ans = self._call_local_ollama(clean)
        if local_ans:
            self.messages.append({"role": "user", "content": clean})
            self.messages.append({"role": "assistant", "content": local_ans})
            return local_ans

        return "Right away, Sir. Processing your request."
