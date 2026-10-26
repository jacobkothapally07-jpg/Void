#!/usr/bin/env python3
import sys
import os
import time
import queue
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
BLOCK_SIZE = 800  # 50ms per audio evaluation slice
SILENCE_TIMEOUT = 0.85  # Natural pause allowance before finalizing sentence
MAX_SPEECH_SECONDS = 15.0
MIN_SPEECH_SECONDS = 0.30

_is_jarvis_sleeping = False
_active_stream = None

def set_jarvis_sleeping(sleeping: bool):
    global _is_jarvis_sleeping, _active_stream
    _is_jarvis_sleeping = sleeping
    if _active_stream is not None:
        try:
            if sleeping and _active_stream.active:
                _active_stream.stop()
                set_widget_state("sleep", "MIC OFF // SLEEPING")
                print("\033[93m[CoreAudio Hardware] Microphone stream stopped (Orange dot OFF).\033[0m")
            elif not sleeping and not _active_stream.active:
                _active_stream.start()
                set_widget_state("idle", "JARVIS // ONLINE")
                print("\033[92m[CoreAudio Hardware] Microphone stream restarted (Orange dot ON).\033[0m")
        except Exception as e:
            print(f"[CoreAudio Power Error] {e}")

def get_jarvis_sleeping() -> bool:
    global _is_jarvis_sleeping
    return _is_jarvis_sleeping

def clean_speech_query(text: str) -> str:
    """Strips conversational leading wake words so natural queries resolve cleanly."""
    clean = text.strip()
    clean = re.sub(r"^(?:(?:hey|ok|okay|hi|hello)\s+)?jarvis[\s,]*", "", clean, flags=re.IGNORECASE).strip()
    return clean

def run_voice_listener():
    print("\033[96m=====================================================\033[0m")
    print("\033[96m   J.A.R.V.I.S. PRO STREAMING VOICE ENGINE ACTIVE   \033[0m")
    print("\033[96m   CoreAudio Ring Stream • Auto-Gain • 0ms Barge-In \033[0m")
    print("\033[96m=====================================================\033[0m\n")

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False

    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        audio_queue.put(indata.flatten().copy())

    global _active_stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK_SIZE,
        callback=audio_callback
    )
    _active_stream = stream
    stream.start()

    ambient_floor = 0.016
    # 400ms pre-speech rolling ring buffer (8 blocks of 50ms)
    pre_speech_ring = collections.deque(maxlen=8)

    # Let startup sounds complete cleanly and flush initial buffer
    time.sleep(0.8)
    while not audio_queue.empty():
        audio_queue.get_nowait()

    was_speaking_prev = False

    while True:
        try:
            if _is_jarvis_sleeping:
                time.sleep(0.3)
                while not audio_queue.empty():
                    audio_queue.get_nowait()
                continue

            currently_speaking = get_is_speaking()

            # 1. WHILE JARVIS IS SPEAKING: Cleanly mute mic input so laptop speakers never loop back
            if currently_speaking:
                was_speaking_prev = True
                while not audio_queue.empty():
                    try:
                        audio_queue.get_nowait()
                    except Exception:
                        break
                time.sleep(0.05)
                continue

            # 2. ECHO DISSIPATION: If Jarvis just finished speaking, clear room reverberation
            if was_speaking_prev and not currently_speaking:
                was_speaking_prev = False
                time.sleep(0.25)
                while not audio_queue.empty():
                    try:
                        audio_queue.get_nowait()
                    except Exception:
                        break
                continue

            try:
                block = audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            rms = float(np.sqrt(np.mean(block**2)))

            # Dynamic calibrated thresholds for MacBook Air mic:
            # Ambient room noise is ~0.015 - 0.018. User speech is 0.150 - 0.400.
            speech_threshold = max(0.035, ambient_floor * 2.2)

            # 3. SILENCE / NOISE GATE
            if rms < speech_threshold:
                ambient_floor = 0.97 * ambient_floor + 0.03 * rms
                pre_speech_ring.append(block)
                continue

            # 4. USER SPEECH ONSET DETECTED
            print(f"\n\033[93m[Speech Detected]\033[0m Energy: {rms:.4f} (Threshold: {speech_threshold:.4f}) -> Buffering sentence...")
            set_widget_state("listening", "Listening to you...")

            speech_blocks = list(pre_speech_ring)
            speech_blocks.append(block)
            pre_speech_ring.clear()

            silence_start = None
            recording_start = time.time()
            # Silence threshold: when audio drops back below 0.026, user has paused
            silence_threshold = max(0.026, ambient_floor * 1.6)
            silence_timeout = 0.70

            while True:
                try:
                    f = audio_queue.get(timeout=0.15)
                except queue.Empty:
                    break

                f_rms = float(np.sqrt(np.mean(f**2)))
                speech_blocks.append(f)

                now = time.time()
                total_duration = now - recording_start

                if f_rms < silence_threshold:
                    if silence_start is None:
                        silence_start = now
                    elif now - silence_start >= silence_timeout:
                        # User has paused naturally for 0.75s -> Sentence complete!
                        break
                else:
                    silence_start = None

                if total_duration >= 10.0:
                    break

            total_speech_len = len(speech_blocks) * (BLOCK_SIZE / float(SAMPLE_RATE))
            if total_speech_len < MIN_SPEECH_SECONDS:
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            # 4. AUDIO NORMALIZATION (Auto-Gain) & IN-MEMORY AUDIO
            full_audio = np.concatenate(speech_blocks)
            max_peak = float(np.max(np.abs(full_audio)))
            if max_peak > 0.005:
                # Normalize peak to 90% full scale so quiet speech is crystal clear
                full_audio = full_audio / max_peak * 0.90
            
            pcm_bytes = (full_audio * 32767.0).astype(np.int16).tobytes()
            audio_data = sr.AudioData(pcm_bytes, SAMPLE_RATE, 2)

            set_widget_state("thinking", "Transcribing speech...")

            # Transcribe with language="en-IN" (optimized for Indian English), fallback to "en-US"
            raw_text = ""
            try:
                raw_text = recognizer.recognize_google(audio_data, language="en-IN").strip()
            except sr.UnknownValueError:
                try:
                    raw_text = recognizer.recognize_google(audio_data, language="en-US").strip()
                except Exception:
                    raw_text = ""
            except Exception:
                try:
                    raw_text = recognizer.recognize_google(audio_data, language="en-US").strip()
                except Exception:
                    raw_text = ""

            if not raw_text:
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            print(f"\n\033[92m[User Spoke]\033[0m \"{raw_text}\"")

            lower = raw_text.lower().strip()
            # Standalone stop/mute commands
            if any(k in lower for k in ["stop", "shut up", "be quiet", "quiet", "stop talking", "stop yapping", "hush", "mute", "silence", "stop it"]):
                stop_speaking()
                set_widget_state("idle", "JARVIS // ONLINE")
                continue

            # Standalone wake/ping
            if lower in ["jarvis", "hey jarvis", "hello jarvis", "hi jarvis", "okay jarvis", "ok jarvis"]:
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
            time.sleep(0.05)

if __name__ == "__main__":
    run_voice_listener()
