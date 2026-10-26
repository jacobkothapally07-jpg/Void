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
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-3-flash-preview"
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
