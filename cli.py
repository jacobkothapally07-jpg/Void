#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.fast_engine import dispatch_fast_action
from brain.llm_client import JarvisBrain
from voice.tts import speak

brain = None

def execute_jarvis_query(query: str, voice_output: bool = True) -> str:
    global brain
    clean = query.strip()
    if not clean:
        return "Standing by, Sir."

    # 1. Fast path (0ms)
    matched, fast_reply = dispatch_fast_action(clean)
    if matched and fast_reply:
        if voice_output:
            speak(fast_reply, async_mode=True)
        return fast_reply

    # 2. Deep Intelligence (Gemini + Tools)
    if brain is None:
        brain = JarvisBrain()
    reply = brain.respond(clean)
    if voice_output:
        speak(reply, async_mode=True)
    return reply

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        ans = execute_jarvis_query(query, voice_output=False)
        print(ans)
    else:
        print("J.A.R.V.I.S. Interactive Shell (Type 'exit' to quit)")
        while True:
            try:
                user_in = input("\nSir > ")
                if user_in.strip().lower() in ["exit", "quit", "q"]:
                    break
                print(f"J.A.R.V.I.S. > {execute_jarvis_query(user_in)}")
            except (KeyboardInterrupt, EOFError):
                break
