#!/usr/bin/env python3
import sys
import os
import time
import tempfile
import urllib.request
import json
import re
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.fast_engine import dispatch_fast_action
from voice.tts import speak_detached, get_is_speaking, stop_speaking, get_current_speaking_text
from hud import set_widget_state

SAMPLE_RATE = 16000
CHUNK_DURATION = 1.8 # Snappy chunk duration for instant interruption (< 2s latency)
SILENCE_THRESHOLD = 0.0035 # Noise gate RMS calibrated for MacBook Air microphone

_is_jarvis_sleeping = False

def set_jarvis_sleeping(sleeping: bool):
    global _is_jarvis_sleeping
    _is_jarvis_sleeping = sleeping

def get_jarvis_sleeping() -> bool:
    global _is_jarvis_sleeping
    return _is_jarvis_sleeping

def is_echo_of_jarvis(user_text: str, jarvis_text: str) -> bool:
    """
    Determines if transcribed microphone input is simply speaker audio leaking from Jarvis's own voice,
    or if it is the user interrupting / commanding Jarvis to stop.
    """
    if not jarvis_text:
        return False
    u = user_text.lower().strip()
    j = jarvis_text.lower().strip()

    # Instant barge-in keywords: ANY of these will ALWAYS interrupt Jarvis
    barge_triggers = [
        "stop", "shut up", "be quiet", "quiet", "wait", "listen", "no", "hold on",
        "cancel", "actually", "jarvis", "hey", "pause", "hush", "mute"
    ]
    if any(trigger in u for trigger in barge_triggers):
        return False

    u_words = set(re.findall(r"\w+", u))
    j_words = set(re.findall(r"\w+", j))
    if not u_words:
        return False

    # If 70% or more of the detected words match what Jarvis is currently reciting, it's echo
    overlap = len(u_words.intersection(j_words)) / len(u_words)
    return overlap >= 0.70

def run_voice_listener():
    print("\033[96m=====================================================\033[0m")
    print("\033[96m   J.A.R.V.I.S. NATIVE DESKTOP VOICE LISTENER ACTIVE\033[0m")
    print("\033[96m   Full-Duplex Barge-In & Interruption Enabled (24/7)\033[0m")
    print("\033[96m=====================================================\033[0m\n")

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 280
    recognizer.dynamic_energy_threshold = True

    while True:
        try:
            if _is_jarvis_sleeping:
                time.sleep(0.4)
                continue

            # Continually record audio from default microphone (NEVER sleep or block when speaking!)
            audio_data = sd.rec(int(CHUNK_DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()

            rms = np.sqrt(np.mean(audio_data**2))
            if rms < SILENCE_THRESHOLD:
                continue

            # Save temporary WAV for STT
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio_data, SAMPLE_RATE)
                tmp_path = tmp.name

            # Transcribe via Google STT API (fast, robust, free)
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio).strip()
                except Exception:
                    text = ""

            try:
                os.remove(tmp_path)
            except Exception:
                pass

            if not text:
                continue

            was_speaking = get_is_speaking()
            current_jarvis_speech = get_current_speaking_text()

            # Check if this speech is an echo of Jarvis's own voice
            if was_speaking and is_echo_of_jarvis(text, current_jarvis_speech):
                # Simply speaker echo from Jarvis's voice, ignore
                continue

            # FULL-DUPLEX BARGE-IN: If Jarvis was speaking and user started talking, SHUT UP IMMEDIATELY!
            if was_speaking:
                print(f"\n\033[91m[Barge-In Interruption!]\033[0m User spoke: \"{text}\" -> Silencing Jarvis immediately.")
                stop_speaking()
                set_widget_state("listening", f"Heard: {text}")

            print(f"\n\033[93m[Jarvis Heard Voice]\033[0m {text}")

            # If user just said stop/shut up/quiet, we already silenced Jarvis, acknowledge cleanly
            lower = text.lower().strip()
            if lower in ["stop", "shut up", "be quiet", "quiet", "stop talking", "hush", "mute", "silence", "jarvis stop"]:
                stop_speaking()
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            # Send query to local Jarvis API
            req = urllib.request.Request(
                "http://127.0.0.1:8080/api/chat",
                data=json.dumps({"message": text}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                reply = res.get("response", "At your service, Sir.")
                print(f"\033[92m[Jarvis Replied]\033[0m {reply}")

        except Exception as e:
            time.sleep(0.4)

if __name__ == "__main__":
    run_voice_listener()
