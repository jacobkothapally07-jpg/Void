import subprocess
import threading

def play_sfx(sfx_name: str = 'blip'):
    def _run():
        try:
            # macOS built-in system sound effects
            sfx_map = {
                'blip': '/System/Library/Sounds/Tink.aiff',
                'startup': '/System/Library/Sounds/Hero.aiff',
                'confirm': '/System/Library/Sounds/Ping.aiff',
                'protocol': '/System/Library/Sounds/Glass.aiff',
                'error': '/System/Library/Sounds/Sosumi.aiff'
            }
            sound_file = sfx_map.get(sfx_name.lower(), '/System/Library/Sounds/Tink.aiff')
            subprocess.run(['afplay', sound_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()
