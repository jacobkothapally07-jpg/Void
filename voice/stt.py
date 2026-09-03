import os
import sys

def listen_from_mic():
    """
    Listens from the default microphone and transcribes speech to text.
    Requires: SpeechRecognition and PyAudio
    """
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("\033[93m[Listening for speech...]\033[0m")
            r.adjust_for_ambient_noise(source, duration=0.6)
            audio = r.listen(source, timeout=8, phrase_time_limit=15)
            print("\033[90m[Processing audio...]\033[0m")
            text = r.recognize_google(audio)
            return text
    except ImportError:
        print("\033[33m[Notice] Voice input requires: pip install SpeechRecognition pyaudio\033[0m")
        return None
    except Exception as e:
        print(f"[STT Error] {e}")
        return None
