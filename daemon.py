import sys
import os
import time
import re
import subprocess
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain import JarvisBrain
from voice import speak
from tools.notification_tools import send_desktop_notification

brain = JarvisBrain()
SAMPLE_RATE = 44100
CHUNK_DURATION = 3.5 # 3.5 second audio chunk
SILENCE_THRESHOLD = 0.012 # RMS volume threshold

def play_chime():
    """Plays subtle macOS tech chime on wake."""
    try:
        subprocess.Popen(["afplay", "/System/Library/Sounds/Tink.aiff"])
    except:
        pass

def listen_and_process():
    print("\033[96m=====================================================\033[0m")
    print("\033[96m   J.A.R.V.I.S. BACKGROUND MAC SERVICE ACTIVE\033[0m")
    print("\033[96m   Listening 24/7 for: \"HEY JARVIS\" or \"JARVIS\"\033[0m")
    print("\033[96m=====================================================\033[0m\n")
    
    speak("Auxiliary background systems initialized. Listening for your command, Sir.", async_mode=True)

    recognizer = sr.Recognizer()

    while True:
        try:
            # 1. Record audio chunk from default microphone
            audio_data = sd.rec(int(CHUNK_DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()

            # 2. Check if volume exceeds background noise threshold
            rms = np.sqrt(np.mean(audio_data**2))
            if rms < SILENCE_THRESHOLD:
                continue

            # 3. Save temporary WAV to transcribe
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                tmp_path = tmp_wav.name
                sf.write(tmp_path, audio_data, SAMPLE_RATE)

            # 4. Transcribe audio
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio).strip()
                except (sr.UnknownValueError, sr.RequestError):
                    text = ""

            try:
                os.remove(tmp_path)
            except:
                pass

            if not text:
                continue

            print(f"\033[90m[Detected Audio] {text}\033[0m")
            lower_text = text.lower()

            # 5. Check for wake word trigger
            if "jarvis" in lower_text or "hey" in lower_text:
                play_chime()
                print(f"\033[92m⚡ Wake Word Triggered: \"{text}\"\033[0m")

                # Extract command after wake word if present
                match = re.search(r"(?:hey\s+)?jarvis[,\s]*(.*)", text, re.IGNORECASE)
                command = match.group(1).strip() if match and match.group(1) else text

                if not command or command.lower() in ["jarvis", "hey jarvis", "hey"]:
                    greeting = "Yes, Sir? How can I help?"
                    print(f"JARVIS > {greeting}\n")
                    speak(greeting, async_mode=False)
                    continue

                send_desktop_notification("J.A.R.V.I.S. Voice", f"Command: {command}")
                response = brain.respond(command)
                print(f"\nJARVIS > {response}\n")
                
                # Speak aloud with neural British voice (synchronously so it does not hear itself)
                speak(response, async_mode=False)

        except KeyboardInterrupt:
            print("\nJARVIS Background Service stopped.")
            break
        except Exception as e:
            time.sleep(0.5)

if __name__ == "__main__":
    listen_and_process()
