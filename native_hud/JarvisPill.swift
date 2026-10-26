import Cocoa
import WebKit
import Speech
import AVFoundation

class SpeechManager: NSObject, SFSpeechRecognizerDelegate {
    let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    let audioEngine = AVAudioEngine()
    var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    var recognitionTask: SFSpeechRecognitionTask?
    var isListening = false
    
    func toggleListening(onText: @escaping (String) -> Void, onStateChange: @escaping (Bool) -> Void) {
        if isListening {
            stopListening()
            onStateChange(false)
        } else {
            do {
                try startListening(onText: onText)
                isListening = true
                onStateChange(true)
            } catch {
                print("Speech recognition failed to start: \(error)")
                onStateChange(false)
            }
        }
    }
    
    func startListening(onText: @escaping (String) -> Void) throws {
        recognitionTask?.cancel()
        recognitionTask = nil
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { return }
        recognitionRequest.shouldReportPartialResults = true
        
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        audioEngine.prepare()
        try audioEngine.start()
        
        recognitionTask = recognizer?.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            if let result = result {
                let transcription = result.bestTranscription.formattedString
                onText(transcription)
            }
            if error != nil || (result?.isFinal ?? false) {
                self?.stopListening()
            }
        }
    }
    
    func stopListening() {
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        isListening = false
    }
}

class JarvisWindowController: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    var window: NSPanel!
    var webView: WKWebView!
    var statusItem: NSStatusItem!
    let speechManager = SpeechManager()
    
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
        let contentRect = NSRect(x: 0, y: 0, width: 660, height: 210)
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
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif; }
            body { background: transparent; padding: 12px; display: flex; justify-content: center; align-items: center; user-select: none; }
            .pill {
                width: 100%;
                background: rgba(13, 17, 23, 0.95);
                backdrop-filter: blur(32px);
                border: 1px solid rgba(255, 170, 0, 0.45);
                box-shadow: 0 16px 45px rgba(0,0,0,0.8), 0 0 30px rgba(255, 170, 0, 0.2);
                border-radius: 26px;
                padding: 14px 22px;
                display: flex;
                flex-direction: column;
                gap: 10px;
                transition: all 0.2s ease;
            }
            .top-bar { display: flex; align-items: center; justify-content: space-between; }
            .brand { font-size: 11px; font-weight: 800; letter-spacing: 2px; color: #ffaa00; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
            .arc-dot { width: 8px; height: 8px; border-radius: 50%; background: #ffaa00; box-shadow: 0 0 10px #ffaa00; }
            .controls { display: flex; align-items: center; gap: 12px; }
            .status { font-size: 10px; color: #00ffaa; letter-spacing: 1px; font-weight: 600; }
            .close-btn { color: rgba(255,255,255,0.4); font-size: 14px; cursor: pointer; transition: color 0.15s; }
            .close-btn:hover { color: #ffffff; }
            
            .input-row { display: flex; align-items: center; gap: 12px; }
            input {
                flex: 1;
                background: transparent;
                border: none;
                outline: none;
                color: #ffffff;
                font-size: 16px;
                font-weight: 500;
                letter-spacing: 0.4px;
            }
            input::placeholder { color: rgba(255,255,255,0.38); }
            
            .mic-btn {
                background: rgba(255, 170, 0, 0.12);
                border: 1px solid rgba(255, 170, 0, 0.3);
                color: #ffaa00;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .mic-btn:hover { background: rgba(255, 170, 0, 0.25); transform: scale(1.05); }
            .mic-btn.active {
                background: #ff3b30;
                border-color: #ff3b30;
                color: #ffffff;
                box-shadow: 0 0 14px #ff3b30;
                animation: pulse 1.2s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.12); }
                100% { transform: scale(1); }
            }
            
            .pills-row { display: flex; gap: 6px; overflow-x: hidden; }
            .action-pill {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.65);
                font-size: 10px;
                font-weight: 500;
                padding: 4px 10px;
                border-radius: 12px;
                cursor: pointer;
                white-space: nowrap;
                transition: all 0.15s ease;
            }
            .action-pill:hover {
                background: rgba(255, 170, 0, 0.15);
                border-color: rgba(255, 170, 0, 0.4);
                color: #ffaa00;
            }
            
            .reply {
                font-size: 13.5px;
                color: #e5ebf2;
                line-height: 1.45;
                padding: 8px 0 2px 0;
                display: none;
                border-top: 1px solid rgba(255, 170, 0, 0.15);
                max-height: 90px;
                overflow-y: auto;
                user-select: text;
            }
        </style>
        </head>
        <body>
        <div class="pill">
            <div class="top-bar">
                <div class="brand">
                    <div class="arc-dot"></div>
                    <span>J.A.R.V.I.S. // AUTONOMOUS OS</span>
                </div>
                <div class="controls">
                    <span class="status" id="status">● READY</span>
                    <span class="close-btn" onclick="hidePill()">✕</span>
                </div>
            </div>
            <div class="input-row">
                <input id="prompt" placeholder="Ask anything, solve code, control apps..." autofocus autocomplete="off" />
                <button class="mic-btn" id="micBtn" onclick="toggleMic()" title="Hold or click to talk">🎙️</button>
            </div>
            <div class="pills-row" id="suggestions">
                <span class="action-pill" onclick="sendQuick('what time is it')">⏱️ Time & Battery</span>
                <span class="action-pill" onclick="sendQuick('solve the coding problem on my screen and paste it')">⚡ Solve Screen Code</span>
                <span class="action-pill" onclick="sendQuick('tile windows side by side')">🪟 Tile Windows</span>
                <span class="action-pill" onclick="sendQuick('what is on my screen right now')">👁️ Watch Screen</span>
            </div>
            <div class="reply" id="reply"></div>
        </div>
        <script>
            const input = document.getElementById('prompt');
            const reply = document.getElementById('reply');
            const status = document.getElementById('status');
            const micBtn = document.getElementById('micBtn');
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && input.value.trim()) {
                    execute(input.value.trim());
                } else if (e.key === 'Escape') {
                    hidePill();
                }
            });
            
            function execute(text) {
                status.innerText = '⚡ EXECUTING...';
                status.style.color = '#ffaa00';
                window.webkit.messageHandlers.jarvis.postMessage({ action: 'execute', query: text });
            }
            
            function sendQuick(text) {
                input.value = text;
                execute(text);
            }
            
            function toggleMic() {
                window.webkit.messageHandlers.jarvis.postMessage({ action: 'toggle_mic' });
            }
            
            function setMicState(active) {
                if (active) {
                    micBtn.classList.add('active');
                    status.innerText = '🔴 LISTENING...';
                    status.style.color = '#ff3b30';
                } else {
                    micBtn.classList.remove('active');
                    status.innerText = '● READY';
                    status.style.color = '#00ffaa';
                }
            }
            
            function setLiveText(text) {
                input.value = text;
            }
            
            function hidePill() {
                window.webkit.messageHandlers.jarvis.postMessage({ action: 'hide' });
            }
            
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
        } else if action == "toggle_mic" {
            speechManager.toggleListening(
                onText: { [weak self] liveText in
                    DispatchQueue.main.async {
                        let escaped = liveText.replacingOccurrences(of: "'", with: "\\'")
                        self?.webView.evaluateJavaScript("setLiveText('\(escaped)')", completionHandler: nil)
                    }
                },
                onStateChange: { [weak self] isListening in
                    DispatchQueue.main.async {
                        self?.webView.evaluateJavaScript("setMicState(\(isListening))", completionHandler: nil)
                    }
                }
            )
        } else if action == "execute", let query = dict["query"] as? String {
            speechManager.stopListening()
            DispatchQueue.main.async {
                self.webView.evaluateJavaScript("setMicState(false)", completionHandler: nil)
            }
            
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
        NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            // Option + Space (keyCode 49 is Space)
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
