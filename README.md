# 🌌 Void — Advanced Autonomous AI Operating System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-white.svg)](https://opensource.org/licenses/MIT)
[![macOS Native](https://img.shields.io/badge/macOS-Sonoma%20%7C%20Sequoia-black.svg)]()
[![Hotkey](https://img.shields.io/badge/Hotkey-⌘⇧V-purple.svg)]()
[![Voice: British Neural](https://img.shields.io/badge/Voice-British%20Paul%20Bettany-black.svg)]()

**Void** is a production-grade, autonomous desktop AI operating system engineered for macOS and iOS. Featuring an interactive 3D Hologram Particle Sphere on pure OLED black, high-fidelity British neural speech synthesis, hardware-level macOS control, and a global mobile remote.

---

## 🌟 Key Capabilities

### 🪐 1. 3D Holographic Particle Matrix
- **Point-Cloud Particle Sphere**: 4,800 starlight points with dense polar caps and concentric horizontal latitude strata rendered natively at 60 FPS.
- **Interactive Orbit**: Click or touch-drag across the sphere to rotate and inspect it in 3D with realistic momentum.
- **Audio & State Reactivity**: Dynamic particle expansion, quantum oscillation, and acoustic ripples during idle, listening, thinking, and speaking states.
- **Global Hotkey**: Press **`⌘⇧V`** (`Cmd + Shift + V`) anywhere on macOS to instantly toggle the Void desktop HUD.

### 🧠 2. Autonomous Execution & Zero-Latency Fast Path
- **Autonomous Execution**: Directly executes real-world actions rather than outputting instructions.
- **Atticus-Style Fast Path (<1ms)**: Immediate hardware controls (lock workstation, acoustic beacon, screen recording, volume adjustment) execute instantly without cloud latency.
- **IRL Slang & Colloquialisms**: Understands casual requests (*"dim the lights"*, *"lock it down"*, *"where is my mac"*, *"solve this code"*).

### 🎙️ 3. High-Fidelity British Neural Speech & Far-Field Voice
- **Ultra-Realistic Voice**: Movie-grade British neural speech (`en-GB-RyanNeural`) with zero-delay streaming.
- **CoreAudio Ring Buffer & Auto-Gain**: 600ms rolling pre-speech ring buffer and 95% peak normalization for crystal-clear microphone pickup.
- **Hardware Mute Gating**: Microphone stream cleanly mutes during speech playback to eliminate acoustic feedback.

### 📱 4. Global Mobile Remote (PWA)
- **Production Edge CDN**: [https://jarvis-mobile-remote.vercel.app](https://jarvis-mobile-remote.vercel.app)
- **Real-Time Remote Control**: Sentry webcam surveillance, workstation lockdown, 100% volume sound beacon, master volume slider, and live system telemetry.

### 🛠️ 5. Native macOS Tools
- **Security & Vision**: Native SAC workstation lock (`login.framework`), Desk Sentry with headless sandbox bypass (`SentryEye.app`), Full-screen vision OCR.
- **Productivity & Hardware**: Apple Notes, Apple Reminders, Calendar event scheduler, Clipboard manager, Master CoreAudio volume sync.
- **Developer Suite**: Automatic screen problem solver and auto-paste, Git commit automation, Terminal execution.

---

## ⌨️ Shortcuts & Hotkeys

| Action | Shortcut / Trigger |
| :--- | :--- |
| **Toggle Void HUD** | **`⌘⇧V`** (`Cmd + Shift + V`) |
| **Voice Wake Word** | `"Void"`, `"Hey Void"`, `"OK Void"` |
| **Instant Mute** | Say *"Quiet"*, *"Stop"*, or tap the Void core |
| **Desk Sentry** | Tap **Desk Sentry** or say *"Sentry Mode"* |
| **Find My Mac** | Tap **Find Mac** or say *"Find my Mac"* |

---

## 🚀 Quick Start

### 1. Setup
```bash
cd jarvis
pip install -r requirements.txt
cp .env.example .env
# Ensure GEMINI_API_KEY is configured in .env
```

### 2. Launch Background Daemon
```bash
./start_background.sh
```

### 3. Open Standalone 3D HUD
Press **`⌘⇧V`** anywhere on your Mac or visit `http://127.0.0.1:8080/widget`.

---

## 📄 License
MIT License. Created for JK Industries.
