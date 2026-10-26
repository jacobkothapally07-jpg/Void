#!/usr/bin/env python3
import sys
import os
import time
import tempfile
import urllib.request
import json
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.fast_engine import dispatch_fast_action
from voice.tts import speak_detached, get_is_speaking

SAMPLE_RATE = 16000
CHUNK_DURATION = 2.8 # Audio chunk duration in seconds
SILENCE_THRESHOLD = 0.0035 # Noise gate RMS calibrated for MacBook Air microphone

def update_widget(state, text=""):
    try:
        url = "http://127.0.0.1:8080/api/chat" # or via direct state if running locally
    except Exception:
        pass

def run_voice_listener():
    print("\033[96m=====================================================\033[0m")
    print("\033[96m   J.A.R.V.I.S. NATIVE DESKTOP VOICE LISTENER ACTIVE\033[0m")
    print("\033[96m   Listening 24/7 on microphone (Google Neural STT)\033[0m")
    print("\033[96m=====================================================\033[0m\n")

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 280
    recognizer.dynamic_energy_threshold = True

    while True:
        try:
            # If Jarvis is speaking, do not listen (ECHO GATE)
            if get_is_speaking():
                time.sleep(0.4)
                continue

            # Record chunk from default microphone
            audio_data = sd.rec(int(CHUNK_DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()

            if get_is_speaking():
                continue

            rms = np.sqrt(np.mean(audio_data**2))
            if rms < SILENCE_THRESHOLD:
                continue

            # Save temporary WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio_data, SAMPLE_RATE)
                tmp_path = tmp.name

            # Transcribe via Google STT API (free, fast, accent-resilient)
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

            print(f"\n\033[93m[Jarvis Heard Voice]\033[0m {text}")

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

            # Wait until speech starts & completes
            time.sleep(1.0)
            while get_is_speaking():
                time.sleep(0.3)

        except Exception as e:
            time.sleep(0.8)

if __name__ == "__main__":
    run_voice_listener()
