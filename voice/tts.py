import subprocess
import re
import threading
import os
import asyncio
import time
import hashlib

current_audio_proc = None
is_speaking_lock = False
current_speaking_text = ""
TTS_CACHE_DIR = "/tmp/jarvis_tts_cache"
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

def stop_speaking():
    global current_audio_proc, is_speaking_lock, current_speaking_text
    is_speaking_lock = False
    current_speaking_text = ""
    try:
        if current_audio_proc and current_audio_proc.poll() is None:
            current_audio_proc.kill()
            current_audio_proc = None
    except Exception:
        pass
    try:
        subprocess.run(["pkill", "-9", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "say"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def is_speaking():
    global current_audio_proc, is_speaking_lock
    if is_speaking_lock:
        return True
    return current_audio_proc is not None and current_audio_proc.poll() is None

def get_is_speaking():
    return is_speaking()

def get_current_speaking_text() -> str:
    global current_speaking_text
    return current_speaking_text

def clean_for_speech(text: str) -> str:
    """Removes markdown symbols, URLs, and code blocks for smooth, natural speech."""
    text = re.sub(r"```.*?```", "code omitted", text, flags=re.DOTALL)
    text = re.sub(r"`.*?`", "", text)
    text = re.sub(r"[*_~#>-]", " ", text)
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = text.replace("J.A.R.V.I.S.", "Jarvis").replace("JARVIS", "Jarvis")
    text = re.sub(r"\s+", " ", text).strip()
    return text

import json
import urllib.request
import ssl
from config import TTS_PROVIDER, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID

def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def _generate_elevenlabs_audio(clean_text: str, output_path: str) -> bool:
    """Generates ultra-realistic voice audio via ElevenLabs API."""
    if not ELEVENLABS_API_KEY:
        return False
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": clean_text,
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.82
        }
    }
    # Append low-latency streaming query param for instant TTFB
    url_fast = f"{url}?optimize_streaming_latency=4"
    try:
        req = urllib.request.Request(url_fast, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=3.5, context=get_ssl_context()) as resp:
            audio_data = resp.read()
            if len(audio_data) > 500:
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                return True
    except Exception as e:
        print(f"[TTS ElevenLabs Notice] {e}")
    return False

def _speak_neural_sync(clean_text: str):
    global current_audio_proc, is_speaking_lock, current_speaking_text
    is_speaking_lock = True
    current_speaking_text = clean_text.lower().strip()
    
    # 0ms Instant Cache Check for previously generated phrases
    text_hash = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
    cached_file = os.path.join(TTS_CACHE_DIR, f"{text_hash}.mp3")
    
    if os.path.exists(cached_file) and os.path.getsize(cached_file) > 100:
        try:
            current_audio_proc = subprocess.Popen(["afplay", cached_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            current_audio_proc.wait()
            is_speaking_lock = False
            current_audio_proc = None
            return
        except Exception:
            pass

    temp_audio = f"/tmp/jarvis_speech_{os.getpid()}_{int(time.time()*1000)}.mp3"
    played_audio = False

    # 1. Primary: ElevenLabs Paul Bettany Voice for ALL phrases
    if TTS_PROVIDER == "elevenlabs" and ELEVENLABS_API_KEY:
        try:
            success = _generate_elevenlabs_audio(clean_text, temp_audio)
            if success and os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 100:
                try:
                    import shutil
                    shutil.copyfile(temp_audio, cached_file)
                except Exception:
                    pass
                current_audio_proc = subprocess.Popen(["afplay", temp_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                current_audio_proc.wait()
                played_audio = True
        except Exception:
            played_audio = False

    # 2. Secondary Fail-Safe: Google British Neural TTS (Unlimited & Free)
    if not played_audio:
        try:
            from gtts import gTTS
            tts = gTTS(text=clean_text, lang="en", tld="co.uk")
            tts.save(temp_audio)
            if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 100:
                if len(clean_text) < 140:
                    try:
                        import shutil
                        shutil.copyfile(temp_audio, cached_file)
                    except Exception:
                        pass
                current_audio_proc = subprocess.Popen(["afplay", temp_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                current_audio_proc.wait()
                played_audio = True
        except Exception:
            played_audio = False
            
    # 3. Tertiary Offline Fallback: macOS Native Daniel
    if not played_audio:
        try:
            current_audio_proc = subprocess.Popen(["say", "-v", "Daniel", "-r", "170", clean_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            current_audio_proc.wait()
        except Exception:
            pass
            
    is_speaking_lock = False
    current_audio_proc = None
    current_speaking_text = ""
    try:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
    except Exception:
        pass

def speak_detached(text: str):
    """Speaks text in a fully detached background process that outlives CLI script termination."""
    clean_text = clean_for_speech(text)
    if not clean_text:
        return
    try:
        subprocess.run(["osascript", "-e", "set volume without output muted"], check=False)
    except Exception:
        pass
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    helper = f"import sys; sys.path.append({repr(repo_dir)}); from voice.tts import _speak_neural_sync; _speak_neural_sync({repr(clean_text)})"
    subprocess.Popen([sys.executable, "-c", helper], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def speak(text: str, voice: str = "en-GB-RyanNeural", async_mode: bool = True):
    """
    Speaks the given text using the ultra-realistic British neural voice (en-GB-RyanNeural - Paul Bettany style),
    falling back reliably to macOS Daniel voice if offline or slow.
    """
    clean_text = clean_for_speech(text)
    if not clean_text:
        return

    # Ensure audio output is unmuted
    try:
        subprocess.run(["osascript", "-e", "set volume without output muted"], check=False)
    except Exception:
        pass

    if async_mode:
        t = threading.Thread(target=_speak_neural_sync, args=(clean_text,), daemon=True)
        t.start()
    else:
        _speak_neural_sync(clean_text)
