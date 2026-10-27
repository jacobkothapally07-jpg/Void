import subprocess
import re
import threading
import os
import asyncio
import time
import hashlib
import json
import urllib.request
import ssl
from config import TTS_PROVIDER, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID

current_audio_proc = None
is_speaking_lock = False
current_speaking_text = ""
import collections
recent_spoken_history = collections.deque(maxlen=8)
TTS_CACHE_DIR = "/tmp/void_tts_cache_ryan"
SPEAKING_LOCK_FILE = "/tmp/void_speaking.lock"
os.makedirs(TTS_CACHE_DIR, exist_ok=True)

def is_recent_echo(text: str) -> bool:
    """Detects whether transcribed text is an echo of Void's own recent spoken output."""
    clean = text.lower().strip()
    if not clean:
        return False
    # Check exact substring or inverted substring match
    for item in recent_spoken_history:
        if clean in item or item in clean:
            return True
        # Check high word overlap (e.g. >= 50% words in common)
        words1 = set(re.findall(r"\w+", clean))
        words2 = set(re.findall(r"\w+", item))
        if len(words1) >= 2 and len(words1.intersection(words2)) / float(len(words1)) >= 0.5:
            return True
    return False

def stop_speaking():
    global current_audio_proc, is_speaking_lock, current_speaking_text
    is_speaking_lock = False
    current_speaking_text = ""
    try:
        if os.path.exists(SPEAKING_LOCK_FILE):
            os.remove(SPEAKING_LOCK_FILE)
    except Exception:
        pass
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
    text = text.replace("J.A.R.V.I.S.", "Void").replace("JARVIS", "Void").replace("Jarvis", "Void")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

_elevenlabs_disabled_until = 0

def _generate_elevenlabs_audio(clean_text: str, output_path: str) -> bool:
    """Generates voice audio via ElevenLabs API if active."""
    global _elevenlabs_disabled_until
    if not ELEVENLABS_API_KEY or time.time() < _elevenlabs_disabled_until:
        return False
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}?optimize_streaming_latency=4"
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
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=3.5, context=get_ssl_context()) as resp:
            audio_data = resp.read()
            if len(audio_data) > 500:
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                return True
    except Exception as e:
        if "401" in str(e) or "403" in str(e):
            _elevenlabs_disabled_until = time.time() + 86400  # Disable for 24h on quota exhaustion
        print(f"[TTS ElevenLabs Notice] {e}")
    return False

def _play_file_with_echo_lock(audio_file: str):
    """Plays audio file through afplay with automatic hardware speaker lock and echo dissipation."""
    global current_audio_proc
    try:
        with open(SPEAKING_LOCK_FILE, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass
    try:
        current_audio_proc = subprocess.Popen(["afplay", audio_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        current_audio_proc.wait()
    finally:
        time.sleep(0.40)  # Room reverberation dissipation
        current_audio_proc = None
        try:
            if os.path.exists(SPEAKING_LOCK_FILE):
                os.remove(SPEAKING_LOCK_FILE)
        except Exception:
            pass

def _speak_neural_sync(clean_text: str):
    global current_audio_proc, is_speaking_lock, current_speaking_text
    is_speaking_lock = True
    current_speaking_text = clean_text.lower().strip()
    recent_spoken_history.append(current_speaking_text)
    
    # Check Voice-Specific Cache (0ms instant playback for repeated responses)
    text_hash = hashlib.md5(clean_text.encode('utf-8')).hexdigest()
    cached_file = os.path.join(TTS_CACHE_DIR, f"ryan_{text_hash}.mp3")
    
    if os.path.exists(cached_file) and os.path.getsize(cached_file) > 100:
        try:
            _play_file_with_echo_lock(cached_file)
            is_speaking_lock = False
            return
        except Exception:
            pass

    temp_audio = f"/tmp/void_speech_{os.getpid()}_{int(time.time()*1000)}.mp3"
    played_audio = False

    # 1. Primary: If explicitly set to elevenlabs and quota available
    if TTS_PROVIDER == "elevenlabs" and ELEVENLABS_API_KEY and time.time() >= _elevenlabs_disabled_until:
        try:
            success = _generate_elevenlabs_audio(clean_text, temp_audio)
            if success and os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 100:
                try:
                    import shutil
                    shutil.copyfile(temp_audio, cached_file)
                except Exception:
                    pass
                _play_file_with_echo_lock(temp_audio)
                played_audio = True
        except Exception:
            played_audio = False

    # 2. Main Consistent Engine: British Neural Ryan (Paul Bettany tone, Free, Unlimited & Identical Every Time)
    if not played_audio:
        try:
            import edge_tts
            
            async def _gen_edge():
                communicate = edge_tts.Communicate(clean_text, "en-GB-RyanNeural", pitch="-2Hz", rate="+3%")
                await communicate.save(temp_audio)
                
            asyncio.run(asyncio.wait_for(_gen_edge(), timeout=12.0))
            if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 100:
                # Studio acoustic mastering filter to match ElevenLabs clarity and presence
                filtered_audio = temp_audio.replace(".mp3", "_studio.mp3")
                try:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", temp_audio, "-af",
                         "equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=220:t=q:w=1:g=1.5,acompressor=threshold=-16dB:ratio=2.5:attack=15:release=120",
                         filtered_audio],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    if os.path.exists(filtered_audio) and os.path.getsize(filtered_audio) > 100:
                        os.replace(filtered_audio, temp_audio)
                except Exception:
                    pass
                try:
                    import shutil
                    shutil.copyfile(temp_audio, cached_file)
                except Exception:
                    pass
                _play_file_with_echo_lock(temp_audio)
                played_audio = True
        except Exception as e:
            played_audio = False

    # 3. Emergency Offline Fallback (only if edge_tts network totally disconnected)
    if not played_audio:
        try:
            try:
                with open(SPEAKING_LOCK_FILE, "w") as f:
                    f.write(str(time.time()))
            except Exception:
                pass
            current_audio_proc = subprocess.Popen(["say", "-v", "Daniel", "-r", "165", clean_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            current_audio_proc.wait()
        except Exception:
            pass
        finally:
            time.sleep(0.40)
            current_audio_proc = None
            try:
                if os.path.exists(SPEAKING_LOCK_FILE):
                    os.remove(SPEAKING_LOCK_FILE)
            except Exception:
                pass
            
    is_speaking_lock = False
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
    Speaks the given text using Void's consistent British neural voice (en-GB-RyanNeural).
    """
    clean_text = clean_for_speech(text)
    if not clean_text:
        return

    try:
        subprocess.run(["osascript", "-e", "set volume without output muted"], check=False)
    except Exception:
        pass

    if async_mode:
        t = threading.Thread(target=_speak_neural_sync, args=(clean_text,), daemon=True)
        t.start()
    else:
        _speak_neural_sync(clean_text)

def prewarm_tts_cache():
    """Pre-caches common Void phrases in background so they play with 0ms delay in the exact same voice."""
    common_phrases = [
        "Void online and operational, Sir. At your service.",
        "Workstation locked down, Sir.",
        "Location beacon disengaged, Sir.",
        "Entering sleep mode, Sir. Wake me via voice or phone remote whenever you need me.",
        "Muted, Sir.",
        "Operation completed successfully, Sir.",
        "Done, Sir.",
        "Workstation location beacon active. Sir, I am right here."
    ]
    def _worker():
        import edge_tts
        for p in common_phrases:
            h = hashlib.md5(p.encode('utf-8')).hexdigest()
            dest = os.path.join(TTS_CACHE_DIR, f"ryan_{h}.mp3")
            if not os.path.exists(dest) or os.path.getsize(dest) < 100:
                try:
                    async def _run(text=p, target=dest):
                        comm = edge_tts.Communicate(text, "en-GB-RyanNeural", pitch="-2Hz", rate="+3%")
                        await comm.save(target)
                    asyncio.run(_run())
                except Exception:
                    pass
    threading.Thread(target=_worker, daemon=True).start()

# Pre-cache common phrases on module load
prewarm_tts_cache()
