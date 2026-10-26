import Cocoa
import WebKit

class JarvisWindowController: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    var window: NSPanel!
    var webView: WKWebView!
    var statusItem: NSStatusItem!
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        setupStatusItem()
        setupWindow()
        registerHotKey()
    }
    
    func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            button.title = "⚡ J"
            button.action = #selector(toggleHUD)
            button.target = self
        }
    }
    
    func setupWindow() {
        let contentRect = NSRect(x: 0, y: 0, width: 620, height: 160)
        window = NSPanel(
            contentRect: contentRect,
            styleMask: [.nonactivatingPanel, .borderless],
            backing: .buffered,
            defer: false
        )
        window.level = .floating
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = true
        window.center()
        
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "jarvis")
        
        webView = WKWebView(frame: contentRect, configuration: config)
        webView.setValue(false, forKey: "drawsBackground")
        window.contentView = webView
        
        let html = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
            body { background: transparent; padding: 12px; display: flex; justify-content: center; align-items: center; }
            .pill {
                width: 100%;
                background: rgba(14, 18, 26, 0.94);
                backdrop-filter: blur(28px);
                border: 1px solid rgba(255, 170, 0, 0.4);
                box-shadow: 0 10px 40px rgba(0,0,0,0.7), 0 0 25px rgba(255, 170, 0, 0.2);
                border-radius: 28px;
                padding: 12px 20px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                transition: all 0.25s ease;
            }
            .top-bar { display: flex; align-items: center; justify-content: space-between; }
            .brand { font-size: 11px; font-weight: 800; letter-spacing: 2.5px; color: #ffaa00; text-transform: uppercase; }
            .status { font-size: 10px; color: #00ffaa; letter-spacing: 1px; }
            .input-row { display: flex; align-items: center; gap: 10px; }
            input {
                flex: 1;
                background: transparent;
                border: none;
                outline: none;
                color: #ffffff;
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }
            input::placeholder { color: rgba(255,255,255,0.35); }
            .reply {
                font-size: 13px;
                color: #e0e6ed;
                line-height: 1.4;
                padding: 6px 0;
                display: none;
                border-top: 1px solid rgba(255, 170, 0, 0.15);
            }
        </style>
        </head>
        <body>
        <div class="pill">
            <div class="top-bar">
                <span class="brand">J.A.R.V.I.S. // AUTONOMOUS OS</span>
                <span class="status" id="status">● READY</span>
            </div>
            <div class="input-row">
                <input id="prompt" placeholder="Say or type command... (e.g. 'what time is it', 'solve coding question', 'find resume')" autofocus autocomplete="off" />
            </div>
            <div class="reply" id="reply"></div>
        </div>
        <script>
            const input = document.getElementById('prompt');
            const reply = document.getElementById('reply');
            const status = document.getElementById('status');
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && input.value.trim()) {
                    const text = input.value.trim();
                    status.innerText = '⚡ EXECUTING...';
                    status.style.color = '#ffaa00';
                    window.webkit.messageHandlers.jarvis.postMessage({ action: 'execute', query: text });
                } else if (e.key === 'Escape') {
                    window.webkit.messageHandlers.jarvis.postMessage({ action: 'hide' });
                }
            });
            
            function showResult(text) {
                status.innerText = '● READY';
                status.style.color = '#00ffaa';
                reply.style.display = 'block';
                reply.innerText = text;
                input.value = '';
            }
        </script>
        </body>
        </html>
        """
        webView.loadHTMLString(html, baseURL: nil)
    }
    
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let dict = message.body as? [String: Any], let action = dict["action"] as? String else { return }
        
        if action == "hide" {
            window.orderOut(nil)
        } else if action == "execute", let query = dict["query"] as? String {
            DispatchQueue.global(qos: .userInitiated).async {
                let pipe = Pipe()
                let process = Process()
                process.executableURL = URL(fileURLWithPath: "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3")
                process.arguments = ["/Users/jacobkothapally/.gemini/antigravity/scratch/jarvis/cli.py", query]
                process.standardOutput = pipe
                process.standardError = pipe
                try? process.run()
                process.waitUntilExit()
                
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                let output = (String(data: data, encoding: .utf8) ?? "Done, Sir.").trimmingCharacters(in: .whitespacesAndNewlines)
                
                DispatchQueue.main.async {
                    let escaped = output.replacingOccurrences(of: "'", with: "\\'").replacingOccurrences(of: "\n", with: " ")
                    self.webView.evaluateJavaScript("showResult('\(escaped)')", completionHandler: nil)
                }
            }
        }
    }
    
    @objc func toggleHUD() {
        if window.isVisible {
            window.orderOut(nil)
        } else {
            window.center()
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
        }
    }
    
    func registerHotKey() {
        // Global monitor for Option+Space to trigger HUD instantly
        NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            if event.modifierFlags.contains(.option) && event.keyCode == 49 {
                DispatchQueue.main.async { self.toggleHUD() }
            }
        }
    }
}

let app = NSApplication.shared
let delegate = JarvisWindowController()
app.delegate = delegate
app.run()
