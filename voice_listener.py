#!/usr/bin/env python3
import sys
import os
import time
import urllib.request
import json
import re
import collections
import numpy as np
import sounddevice as sd
import speech_recognition as sr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice.tts import get_is_speaking, stop_speaking, get_current_speaking_text
from hud import set_widget_state

SAMPLE_RATE = 16000
FRAME_MS = 100 # 100ms per audio evaluation slice
FRAME_SAMPLES = int(SAMPLE_RATE * (FRAME_MS / 1000.0)) # 1600 samples

# Natural speech pauses: Allow user 0.95 seconds of breathing / pause time before ending sentence
SILENCE_TIMEOUT = 0.95 
MAX_RECORDING_SECONDS = 14.0
MIN_SPEECH_SECONDS = 0.35 # Filters out short clicks or keyboard taps

_is_jarvis_sleeping = False

def set_jarvis_sleeping(sleeping: bool):
    global _is_jarvis_sleeping
    _is_jarvis_sleeping = sleeping

def get_jarvis_sleeping() -> bool:
    global _is_jarvis_sleeping
    return _is_jarvis_sleeping

def is_echo_of_jarvis(user_text: str, jarvis_text: str) -> bool:
    """
    Prevents Jarvis from replying to his own voice if mic picks up speaker output.
    """
    if not jarvis_text:
        return False
    u = user_text.lower().strip()
    j = jarvis_text.lower().strip()

    # Never consider these barge-in commands as echo
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

    overlap = len(u_words.intersection(j_words)) / len(u_words)
    return overlap >= 0.70

def clean_speech_query(text: str) -> str:
    """Strips conversational leading wake words so natural queries resolve cleanly."""
    clean = text.strip()
    # Strip leading "hey jarvis", "jarvis please", "ok jarvis", "jarvis"
    clean = re.sub(r"^(?:(?:hey|ok|okay|hi|hello)\s+)?jarvis[\s,]*", "", clean, flags=re.IGNORECASE).strip()
    return clean

def run_voice_listener():
    print("\033[96m=====================================================\033[0m")
    print("\033[96m   J.A.R.V.I.S. SMART STREAMING VOICE ENGINE ACTIVE\033[0m")
    print("\033[96m   Continuous VAD • Natural Pause Flow • 0ms Barge-In\033[0m")
    print("\033[96m=====================================================\033[0m\n")

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False
    
    ambient_floor = 0.015
    pre_speech_ring = collections.deque(maxlen=3) # 300ms pre-speech buffer

    while True:
        try:
            if _is_jarvis_sleeping:
                time.sleep(0.4)
                continue

            # Record a snappy 100ms frame
            frame = sd.rec(FRAME_SAMPLES, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()
            
            frame_flat = frame.flatten()
            rms = float(np.sqrt(np.mean(frame_flat**2)))

            currently_speaking = get_is_speaking()

            # Dynamic calibrated thresholds:
            # When quiet: speech threshold is ~0.042
            # When Jarvis is speaking through speakers: barge-in threshold is ~0.090
            speech_threshold = max(0.040, ambient_floor * 2.5)
            barge_in_threshold = max(0.090, ambient_floor * 4.2)

            # 1. BARGE-IN CHECK: If Jarvis is speaking, only react if user talks over him
            if currently_speaking:
                if rms > barge_in_threshold:
                    print(f"\n\033[91m[Instant Barge-In!]\033[0m Voice energy ({rms:.4f}) detected while Jarvis speaking -> Muting immediately.")
                    stop_speaking()
                    currently_speaking = False
                else:
                    # Speaker audio bleed; do not record
                    continue

            # 2. SILENCE CHECK: Ambient background noise
            if rms < speech_threshold:
                ambient_floor = 0.96 * ambient_floor + 0.04 * rms
                pre_speech_ring.append(frame_flat)
                continue

            # 3. SPEECH ONSET CONFIRMED: Collect the entire natural sentence
            print(f"\n\033[93m[Speech Detected]\033[0m Energy: {rms:.4f} (Threshold: {speech_threshold:.4f}) -> Buffering sentence...")
            set_widget_state("listening", "Listening to you...")

            speech_frames = list(pre_speech_ring)
            speech_frames.append(frame_flat)
            pre_speech_ring.clear()

            silence_start_time = None
            recording_start_time = time.time()

            while True:
                # Record next 100ms
                frame = sd.rec(FRAME_SAMPLES, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
                sd.wait()
                f_flat = frame.flatten()
                f_rms = float(np.sqrt(np.mean(f_flat**2)))
                speech_frames.append(f_flat)

                now = time.time()
                total_duration = now - recording_start_time

                # Check if this frame is silence
                if f_rms < speech_threshold:
                    if silence_start_time is None:
                        silence_start_time = now
                    elif now - silence_start_time >= SILENCE_TIMEOUT:
                        # User has paused naturally for 0.95s -> Sentence complete!
                        break
                else:
                    # User is actively speaking, reset silence timer
                    silence_start_time = None

                # Hard cutoff if user talks continuously for 14 seconds
                if total_duration >= MAX_RECORDING_SECONDS:
                    break

            total_speech_len = len(speech_frames) * (FRAME_MS / 1000.0)
            if total_speech_len < MIN_SPEECH_SECONDS:
                # Too short (single key click or cough), ignore cleanly
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            # 3. CONVERT BUFFER TO IN-MEMORY AUDIO FOR 100% ACCURATE STT
            full_audio = np.concatenate(speech_frames)
            # Normalize and clamp to 16-bit PCM
            full_audio = np.clip(full_audio, -1.0, 1.0)
            pcm_bytes = (full_audio * 32767.0).astype(np.int16).tobytes()

            audio_data = sr.AudioData(pcm_bytes, SAMPLE_RATE, 2)
            set_widget_state("thinking", "Transcribing speech...")

            try:
                raw_text = recognizer.recognize_google(audio_data).strip()
            except sr.UnknownValueError:
                set_widget_state("idle", "JARVIS // ONLINE")
                continue
            except Exception as e:
                print(f"[STT Error] {e}")
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            if not raw_text:
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            # Check if this speech is an echo of Jarvis's previous sentence
            last_spoken = get_current_speaking_text()
            if is_echo_of_jarvis(raw_text, last_spoken):
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            print(f"\n\033[92m[User Spoke]\033[0m \"{raw_text}\"")

            lower = raw_text.lower().strip()
            # If user said stop/shut up/quiet:
            if lower in ["stop", "shut up", "be quiet", "quiet", "stop talking", "hush", "mute", "silence", "jarvis stop", "stop it"]:
                stop_speaking()
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            # If user just called "Jarvis" or "Hey Jarvis" alone:
            if lower in ["jarvis", "hey jarvis", "hello jarvis", "hi jarvis", "okay jarvis", "ok jarvis"]:
                from brain.persona import get_system_prompt
                from voice.sound_effects import play_repulsor_wake
                play_repulsor_wake()
                req = urllib.request.Request(
                    "http://127.0.0.1:8080/api/chat",
                    data=json.dumps({"message": "hey jarvis"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                try:
                    urllib.request.urlopen(req, timeout=5)
                except Exception:
                    pass
                continue

            # Clean query and send to Jarvis API
            processed_query = clean_speech_query(raw_text)
            if not processed_query:
                processed_query = raw_text

            req = urllib.request.Request(
                "http://127.0.0.1:8080/api/chat",
                data=json.dumps({"message": processed_query}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                reply = res.get("response", "At your service, Sir.")
                print(f"\033[96m[Jarvis Replied]\033[0m {reply}")

        except Exception as e:
            time.sleep(0.1)

if __name__ == "__main__":
    run_voice_listener()
