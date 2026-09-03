import sys
import os
import readline

# Add current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain import JarvisBrain
from config import LLM_PROVIDER, GEMINI_API_KEY, NTFY_TOPIC
from voice import speak, listen_from_mic

def print_banner():
    banner = """
  ======================================================
      J.A.R.V.I.S. Personal System Assistant
      [Just A Rather Very Intelligent System]
  ======================================================
"""
    print(banner)
    print(f"Provider: {LLM_PROVIDER.upper()} | Voice Engine: Daniel (macOS Native)")
    print(f"Mobile Topic: {NTFY_TOPIC}")
    print("Type your request, or type 'mic' to speak via microphone.")
    print("Type 'exit' or 'quit' to terminate session.\n")

def main():
    print_banner()
    brain = JarvisBrain()
    
    # Startup voice greeting
    speak("Auxiliary systems online. At your service, Sir.", async_mode=True)

    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue

            # Voice command via mic
            if user_input.lower() in ["mic", "listen", "voice", "talk"]:
                voice_text = listen_from_mic()
                if voice_text:
                    print(f"You (Voice) > {voice_text}")
                    user_input = voice_text
                else:
                    continue

            if user_input.lower() in ["exit", "quit", "shutdown"]:
                farewell = "Powering down auxiliary systems. Have a pleasant day, Sir."
                print(f"\nJARVIS > {farewell}")
                speak(farewell)
                break

            response = brain.respond(user_input)
            print(f"\nJARVIS > {response}\n")
            
            # Speak response out loud in JARVIS voice
            speak(response, async_mode=True)

        except (KeyboardInterrupt, EOFError):
            print("\n\nJARVIS: Session terminated.")
            break

if __name__ == "__main__":
    main()
