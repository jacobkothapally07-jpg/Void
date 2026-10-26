#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.fast_engine import dispatch_fast_action
from brain.llm_client import JarvisBrain
from voice.tts import speak, speak_detached

brain = None

def execute_jarvis_query(query: str, voice_output: bool = True) -> str:
    global brain
    clean = query.strip()
    if not clean:
        return "Standing by, Sir."

    # 1. Fast path (0ms native deterministic engine)
    matched, fast_reply = dispatch_fast_action(clean)
    if matched and fast_reply:
        if voice_output:
            speak_detached(fast_reply)
        return fast_reply

    # 2. Deep Intelligence (Gemini 3.1 Flash Lite + Multi-tool reasoning)
    if brain is None:
        brain = JarvisBrain()
    reply = brain.respond(clean)
    if voice_output:
        speak_detached(reply)
    return reply

if __name__ == "__main__":
    args = sys.argv[1:]
    voice = True
    if "--no-voice" in args:
        voice = False
        args.remove("--no-voice")
    elif "--silent" in args:
        voice = False
        args.remove("--silent")

    if args:
        query = " ".join(args)
        ans = execute_jarvis_query(query, voice_output=voice)
        print(ans)
    else:
        print("J.A.R.V.I.S. Interactive Shell (Type 'exit' to quit)")
        while True:
            try:
                user_in = input("\nSir > ")
                if user_in.strip().lower() in ["exit", "quit", "q"]:
                    break
                print(f"J.A.R.V.I.S. > {execute_jarvis_query(user_in, voice_output=voice)}")
            except (KeyboardInterrupt, EOFError):
                break
