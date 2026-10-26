import os
import wave
import math
import struct
import subprocess
import threading

SOUNDS_DIR = os.path.join(os.path.dirname(__file__), "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)

def _generate_wav(filename: str, samples: list, sample_rate: int = 44100):
    path = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
        
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)        # Mono
        wf.setsampwidth(2)        # 16-bit
        wf.setframerate(sample_rate)
        # Pack samples to 16-bit PCM
        raw_data = bytearray()
        for s in samples:
            clamped = max(-32767, min(32767, int(s * 32767.0)))
            raw_data.extend(struct.pack('<h', clamped))
        wf.writeframes(raw_data)
    return path

def ensure_sound_effects():
    """Generates authentic Marvel Mark VII sound effects dynamically."""
    sample_rate = 44100
    
    # 1. Repulsor Wake: Rising power hum with resonant harmonic
    repulsor_path = os.path.join(SOUNDS_DIR, "repulsor_wake.wav")
    if not os.path.exists(repulsor_path):
        duration = 0.65
        total_samples = int(sample_rate * duration)
        samples = []
        for i in range(total_samples):
            t = i / sample_rate
            # Frequency sweeps from 180Hz up to 880Hz
            progress = t / duration
            freq = 180.0 + 700.0 * (progress ** 2.2)
            # Harmonic overtone
            env = math.sin(math.pi * progress) ** 0.5
            s = 0.6 * math.sin(2.0 * math.pi * freq * t) + 0.3 * math.sin(4.0 * math.pi * freq * t)
            # Sub-bass warmth
            s += 0.25 * math.sin(2.0 * math.pi * (freq * 0.5) * t)
            samples.append(s * env * 0.8)
        _generate_wav("repulsor_wake.wav", samples, sample_rate)

    # 2. HUD Chirp: Dual-tone crystal digital tap
    hud_path = os.path.join(SOUNDS_DIR, "hud_chirp.wav")
    if not os.path.exists(hud_path):
        duration = 0.12
        total_samples = int(sample_rate * duration)
        samples = []
        for i in range(total_samples):
            t = i / sample_rate
            decay = math.exp(-28.0 * t)
            f1, f2 = 1760.0, 3520.0  # Crisp digital tones
            s = 0.5 * math.sin(2.0 * math.pi * f1 * t) + 0.35 * math.sin(2.0 * math.pi * f2 * t)
            samples.append(s * decay * 0.7)
        _generate_wav("hud_chirp.wav", samples, sample_rate)

    # 3. Target Lock: Tactical rapid double-chirp
    lock_path = os.path.join(SOUNDS_DIR, "target_lock.wav")
    if not os.path.exists(lock_path):
        duration = 0.22
        total_samples = int(sample_rate * duration)
        samples = []
        for i in range(total_samples):
            t = i / sample_rate
            decay1 = math.exp(-35.0 * t) if t < 0.1 else 0
            t2 = t - 0.11
            decay2 = math.exp(-35.0 * t2) if t2 >= 0 else 0
            s = 0.5 * math.sin(2.0 * math.pi * 2200.0 * t) * decay1 + 0.6 * math.sin(2.0 * math.pi * 2640.0 * t) * decay2
            samples.append(s * 0.75)
        _generate_wav("target_lock.wav", samples, sample_rate)

    # 4. Protocol Chime: Majestic Mark VII protocol deployment chord
    chime_path = os.path.join(SOUNDS_DIR, "protocol_chime.wav")
    if not os.path.exists(chime_path):
        duration = 0.75
        total_samples = int(sample_rate * duration)
        samples = []
        # Chord frequencies: C5 (523.25), G5 (783.99), C6 (1046.50)
        for i in range(total_samples):
            t = i / sample_rate
            decay = math.exp(-4.5 * t)
            s = 0.4 * math.sin(2.0 * math.pi * 523.25 * t)
            s += 0.35 * math.sin(2.0 * math.pi * 783.99 * t)
            s += 0.3 * math.sin(2.0 * math.pi * 1046.50 * t)
            samples.append(s * decay * 0.8)
        _generate_wav("protocol_chime.wav", samples, sample_rate)

ensure_sound_effects()

def play_fx(effect_name: str, volume: float = 0.7):
    """Plays an Iron Man sound effect asynchronously via native macOS afplay."""
    wav_file = os.path.join(SOUNDS_DIR, f"{effect_name}.wav")
    if not os.path.exists(wav_file):
        ensure_sound_effects()
        
    if os.path.exists(wav_file):
        def _play():
            try:
                subprocess.run(["afplay", "-v", str(volume), wav_file], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        t = threading.Thread(target=_play, daemon=True)
        t.start()

def play_repulsor_wake():
    play_fx("repulsor_wake", volume=0.85)

def play_hud_chirp():
    play_fx("hud_chirp", volume=0.6)

def play_target_lock():
    play_fx("target_lock", volume=0.7)

def play_protocol_chime():
    play_fx("protocol_chime", volume=0.8)
