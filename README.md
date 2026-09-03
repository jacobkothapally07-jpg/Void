# 🛡️ J.A.R.V.I.S. — Advanced Autonomous AI Operating Companion

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](https://opensource.org/licenses/MIT)
[![macOS Native](https://img.shields.io/badge/macOS-Sonoma%20%7C%20Sequoia-black.svg)]()
[![Voice: Paul Bettany Neural](https://img.shields.io/badge/Voice-British%20Paul%20Bettany-orange.svg)]()

**J.A.R.V.I.S.** (*Just A Rather Very Intelligent System*) is a production-grade, autonomous desktop AI companion engineered for macOS and iOS. Powered by Google Gemini with multi-model fallback and high-fidelity British neural speech synthesis, J.A.R.V.I.S. executes real-world actions, controls system hardware, automates productivity tools, and responds in 1–2 crisp, witty sentences.

---

## 🌟 Key Capabilities

### 🧠 1. True Pro Autonomy & IRL Slang Comprehension
- **Autonomous Execution**: Executes actions directly instead of returning instructions.
- **Natural Language & Slang**: Understands casual colloquialisms (*"dim the lights"*, *"lock it down"*, *"how much juice left"*, *"put on some tracks"*).
- **Fast 1–2 Sentence Delivery**: Paul Bettany personality—polite, sharp, witty, and concise.

### 🎙️ 2. High-Fidelity British Neural Speech & Instant Stop
- **Neural Voice**: Ultra-realistic `en-GB-RyanNeural` movie-grade voice with automatic fallback to macOS native `Daniel`.
- **Instant Barge-In**: Hardware audio cancellation in < 30ms on *"Stop"* or *"Quiet"*.
- **Echo Gating**: Microphone automatically mutes during speech playback to prevent self-looping.

### 📱 3. Multi-Channel Mobile Wakeup (iOS / Siri / Watch)
- **Bonjour mDNS**: `http://jacobs-MacBook-Air.local:8080/api/initiate` (never breaks across DHCP IP shifts).
- **Global Cloud Bridge**: `https://ntfy.sh/jk_jarvis_wakeup` (wake your workstation from anywhere in the world on 5G).

### 🛠️ 4. 28+ Native macOS Tools
- **Productivity**: Apple Notes creator, Clipboard manager (`pbcopy`/`pbpaste`), Apple Reminders, Apple Calendar event scheduler, Mail scanner.
- **System Automation**: Volume control, Dark mode toggle, Lock screen, Sleep display, Empty trash, High-res screenshots, Battery & Hardware diagnostics.
- **Media & Web**: Direct YouTube / Spotify video & music auto-play, Live DuckDuckGo & Wikipedia web crawler.
- **Vision & Security**: FaceTime HD camera Sentry Mode intruder detection, Full-screen window OCR & code analysis.
- **Location & Time**: Live physical geolocation (GPS/IP) and local time detection.

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/jarvis.git
cd jarvis
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY in .env
```

### 2. Launch Background Daemon
```bash
./start_background.sh
```

### 3. Open Standalone 3D HUD
Double-click `JARVIS.app` or open `http://127.0.0.1:8080` in your browser.

---

## 📱 iPhone Shortcut Setup

1. Open **Shortcuts** app on iPhone.
2. Add action: **Get Contents of URL**.
3. URL: `http://jacobs-MacBook-Air.local:8080/api/initiate` (Method: `GET`).
4. Rename shortcut to **Initiate Jarvis** and add to Home Screen or say *"Hey Siri, Initiate Jarvis"*.

---

## 📄 License
MIT License. Created for JK Industries.
