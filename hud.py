_last_hud_wakeup = 0
_widget_state = {"state": "idle", "text": "JARVIS // ONLINE"}

def set_widget_state(state, text=""):
    global _widget_state
    _widget_state = {"state": state, "text": text}
import subprocess

def launch_hud_window(port=8080):
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    profile_dir = os.path.expanduser("~/.jarvis_chrome_app_profile")
    url = f"http://127.0.0.1:{port}"
    if os.path.exists(chrome_path):
        flags = [
            chrome_path,
            f"--app={url}",
            f"--user-data-dir={profile_dir}",
            "--use-fake-ui-for-media-stream",
            "--autoplay-policy=no-user-gesture-required",
            "--enable-features=OverlayScrollbar",
            "--window-size=1150,850",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        try:
            subprocess.Popen(flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            pass
    try:
        subprocess.run(["open", "-a", "Google Chrome", url], check=False)
    except Exception:
        subprocess.run(["open", url], check=False)

import http.server
import socketserver
import json
import sys
import os
import webbrowser
import threading
import time
import mimetypes

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain import JarvisBrain
from brain.fast_engine import dispatch_fast_action
from voice import speak
from voice.tts import stop_speaking, get_is_speaking
from tools.system_tools import get_system_health

brain = JarvisBrain()
PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

class JarvisHTTPHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        clean_path = self.path.split("?")[0]
        if clean_path in ["/", "/index.html"]:
            clean_path = "/index.html"
        elif clean_path in ["/widget", "/widget.html"]:
            clean_path = "/widget.html"
            
        if clean_path in ["/api/wakeup", "/api/initiate"]:
            global _last_hud_wakeup
            now = time.time()
            if now - _last_hud_wakeup < 6:
                self._send_json({"status": "debounced", "message": "Already initiated"})
                return
            _last_hud_wakeup = now
            try:
                subprocess.run(["osascript", "-e", "set volume output volume 80", "-e", "set volume without output muted"], check=False)
                launch_hud_window(PORT)
            except Exception:
                pass
            speak("Neural matrix online and active on your workstation, Sir. At your service.", async_mode=True)
            self._send_json({"status": "success", "message": "J.A.R.V.I.S. initiated"})
            return
        elif clean_path == "/api/status" or clean_path == "/api/health":
            from tools.coding_solver_tools import get_watch_screen_status
            self._send_json({
                "status": "online",
                "system": "J.A.R.V.I.S.",
                "owner": "Jacob Kothapally",
                "version": "3.0-Autonomous",
                "watch_screen": get_watch_screen_status(),
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            return
        elif clean_path == "/api/toggle_watch_screen":
            from tools.coding_solver_tools import toggle_watch_screen, get_watch_screen_status
            from voice.sound_effects import play_hud_chirp
            play_hud_chirp()
            new_state = not get_watch_screen_status()
            res = toggle_watch_screen(new_state)
            self._send_json(res)
            return
        elif clean_path == "/api/solve_screen":
            from tools.coding_solver_tools import solve_and_paste_code
            from voice.sound_effects import play_target_lock
            play_target_lock()
            res = solve_and_paste_code(auto_paste=True)
            self._send_json(res)
            return
        elif clean_path == "/api/speaking_status":
            self._send_json({"is_speaking": get_is_speaking()})
            return
        elif clean_path == "/api/widget_state":
            global _widget_state
            self._send_json(_widget_state)
            return
        elif clean_path == "/api/stats":
            stats = get_system_health()
            self._send_json(stats)
            return
        elif clean_path == "/api/sleep":
            from voice_listener import set_jarvis_sleeping
            set_jarvis_sleeping(True)
            set_widget_state("sleep", "Entering sleep mode...")
            self._send_json({"status": "success", "mode": "sleep"})
            return
        elif clean_path == "/api/wake":
            from voice_listener import set_jarvis_sleeping
            from voice.sound_effects import play_repulsor_wake
            play_repulsor_wake()
            set_jarvis_sleeping(False)
            set_widget_state("idle", "JARVIS // ONLINE")
            speak("Online and operational, Sir. At your service.", async_mode=True)
            self._send_json({"status": "success", "mode": "awake"})
            return
        elif clean_path == "/api/shutdown":
            self._send_json({"status": "success", "message": "shutting down"})
            def _exit_get():
                try:
                    speak("Powering down auxiliary systems. Have a pleasant evening, Sir.", async_mode=False)
                except Exception:
                    pass
                time.sleep(0.5)
                try:
                    subprocess.run(["pkill", "-9", "-f", "JarvisWidget"], check=False)
                    subprocess.run(["pkill", "-INT", "-f", "screencapture -v"], check=False)
                except Exception:
                    pass
                os._exit(0)
            threading.Thread(target=_exit_get, daemon=True).start()
            return

        # Serve static assets from WEB_DIR
        file_path = os.path.join(WEB_DIR, clean_path.lstrip("/"))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                if file_path.endswith(".js"): mime_type = "application/javascript"
                elif file_path.endswith(".png"): mime_type = "image/png"
                elif file_path.endswith(".webp"): mime_type = "image/webp"
                elif file_path.endswith(".mp3"): mime_type = "audio/mpeg"
                elif file_path.endswith(".css"): mime_type = "text/css"
                else: mime_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            if file_path.endswith(".html"):
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
            else:
                self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                body = json.loads(post_data.decode("utf-8"))
                user_msg = body.get("message", "")
                print(f"\n\033[92m[User Query] {user_msg}\033[0m")
                from voice.sound_effects import play_hud_chirp
                play_hud_chirp()
                set_widget_state("thinking", f"Executing: {user_msg}")
                
                # 1. Fast Native Dispatch (< 1ms, Atticus-Mac style, zero cloud lag)
                matched, fast_reply = dispatch_fast_action(user_msg)
                if matched and fast_reply:
                    set_widget_state("speaking", fast_reply)
                    speak(fast_reply, async_mode=True)
                    self._send_json({"response": fast_reply, "status": "success", "fast_path": True})
                    def reset_later():
                        time.sleep(3.5)
                        set_widget_state("idle", "JARVIS // ONLINE")
                    threading.Thread(target=reset_later, daemon=True).start()
                    return

                # 2. Deep Intelligence (Gemini + Multi-Tool reasoning)
                response = brain.respond(user_msg)
                if not response:
                    response = "Operation completed successfully, Sir."
                
                set_widget_state("speaking", response)
                speak(response, async_mode=True)
                def reset_deep():
                    time.sleep(5.0)
                    set_widget_state("idle", "JARVIS // ONLINE")
                threading.Thread(target=reset_deep, daemon=True).start()
                
                # Return JSON response immediately
                self._send_json({"response": response, "status": "success"})
            except Exception as e:
                err_reply = "Auxiliary neural channel reconnected. Online and ready, Sir."
                speak(err_reply, async_mode=True)
                self._send_json({"response": err_reply, "status": "fallback"})
                
        elif self.path in ["/api/wakeup", "/api/initiate"]:
            global _last_hud_wakeup
            now = time.time()
            if now - _last_hud_wakeup < 6:
                self._send_json({"status": "debounced", "message": "Already initiated"})
                return
            _last_hud_wakeup = now
            try:
                subprocess.run(["osascript", "-e", "set volume output volume 80", "-e", "set volume without output muted"], check=False)
                launch_hud_window(PORT)
            except Exception:
                pass
            speak("Neural matrix online and active on your workstation, Sir. At your service.", async_mode=True)
            self._send_json({"status": "success", "message": "J.A.R.V.I.S. initiated"})
            return
            
        elif self.path == "/api/stop":
            stop_speaking()
            self._send_json({"status": "success", "message": "interrupted"})
            
        elif self.path == "/api/shutdown":
            self._send_json({"status": "success", "message": "shutting down"})
            def _exit():
                try:
                    speak("Powering down auxiliary systems. Have a pleasant evening, Sir.", async_mode=False)
                except Exception:
                    pass
                time.sleep(0.5)
                try:
                    subprocess.run(["pkill", "-9", "-f", "JarvisWidget"], check=False)
                    subprocess.run(["pkill", "-INT", "-f", "screencapture -v"], check=False)
                except Exception:
                    pass
                # Unload any launchd plist so macOS launchd does not resurrect a duplicate instance
                try:
                    plist = os.path.expanduser("~/Library/LaunchAgents/com.jk.jarvis.daemon.plist")
                    subprocess.run(["launchctl", "unload", plist], capture_output=True)
                except Exception:
                    pass
                os._exit(0)
            threading.Thread(target=_exit, daemon=True).start()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

def run_server(auto_open_browser=True):
    global PORT
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    httpd = None
    selected_port = PORT

    for p in range(PORT, PORT + 10):
        try:
            httpd = socketserver.ThreadingTCPServer(("0.0.0.0", p), JarvisHTTPHandler)
            selected_port = p
            break
        except OSError:
            continue

    if not httpd:
        print("[Error] Could not bind to any port from 8080 to 8090.")
        return

    PORT = selected_port

    if auto_open_browser:
        def open_browser():
            time.sleep(0.5)
            webbrowser.open(f"http://127.0.0.1:{PORT}")
        threading.Thread(target=open_browser, daemon=True).start()

    with httpd:
        print(f"\n\033[96m======================================================\033[0m")
        print(f"\033[96m  J.A.R.V.I.S. Movie HUD & Neural Voice Engine Online!\033[0m")
        print(f"\033[92m  URL: http://127.0.0.1:{PORT}\033[0m")
        print(f"\033[96m======================================================\033[0m\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nHUD shutting down.")

if __name__ == "__main__":
    run_server()
