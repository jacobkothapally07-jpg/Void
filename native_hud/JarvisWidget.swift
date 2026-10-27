import Cocoa
import WebKit
import Carbon
import AVFoundation

class FloatingWidgetPanel: NSPanel {
    override var canBecomeKey: Bool { return true }
    override var canBecomeMain: Bool { return true }
}

struct HotKeyConfig: Codable {
    var label: String
    var keyCode: UInt32
    var modifiers: UInt32
}

func createWavData(from pcmData: Data, sampleRate: Int = 16000, channels: Int = 1) -> Data {
    var header = Data()
    let totalDataLen = Int32(pcmData.count)
    let totalAudioLen = totalDataLen + 36
    let byteRate = Int32(sampleRate * channels * 2)
    
    // RIFF header
    header.append(contentsOf: [0x52, 0x49, 0x46, 0x46]) // "RIFF"
    var v32 = totalAudioLen.littleEndian
    header.append(Data(bytes: &v32, count: 4))
    header.append(contentsOf: [0x57, 0x41, 0x56, 0x45]) // "WAVE"
    
    // fmt subchunk
    header.append(contentsOf: [0x66, 0x6d, 0x74, 0x20]) // "fmt "
    var subchunk1Size: Int32 = 16
    header.append(Data(bytes: &subchunk1Size, count: 4))
    var audioFormat: Int16 = 1 // PCM
    header.append(Data(bytes: &audioFormat, count: 2))
    var numChannels: Int16 = Int16(channels)
    header.append(Data(bytes: &numChannels, count: 2))
    var sRate: Int32 = Int32(sampleRate)
    header.append(Data(bytes: &sRate, count: 4))
    var bRate: Int32 = byteRate
    header.append(Data(bytes: &bRate, count: 4))
    var blockAlign: Int16 = Int16(channels * 2)
    header.append(Data(bytes: &blockAlign, count: 2))
    var bitsPerSample: Int16 = 16
    header.append(Data(bytes: &bitsPerSample, count: 2))
    
    // data subchunk
    header.append(contentsOf: [0x64, 0x61, 0x74, 0x61]) // "data"
    var vDataLen = totalDataLen.littleEndian
    header.append(Data(bytes: &vDataLen, count: 4))
    
    var full = header
    full.append(pcmData)
    return full
}

class JarvisWidgetController: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    static var shared: JarvisWidgetController?
    
    var window: FloatingWidgetPanel!
    var webView: WKWebView!
    var statusItem: NSStatusItem!
    var hotKeyRefs: [EventHotKeyRef] = []
    var lastToggleTime: TimeInterval = 0
    
    // Native CoreAudio Engine
    let audioEngine = AVAudioEngine()
    var isAudioRecording = false
    var speechPcmBuffer = Data()
    var isUserSpeaking = false
    var silenceStart: TimeInterval? = nil
    var speechStartTime: TimeInterval = 0
    var converter: AVAudioConverter? = nil
    let audioLock = NSLock()
    
    let configFile = NSString(string: "~/.jarvis_hotkey.json").expandingTildeInPath
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        let lockPath = "/tmp/jarvis_widget.lock"
        let myPid = ProcessInfo.processInfo.processIdentifier
        if let existingPidStr = try? String(contentsOfFile: lockPath, encoding: .utf8),
           let existingPid = Int32(existingPidStr.trimmingCharacters(in: .whitespacesAndNewlines)),
           existingPid != myPid {
            if kill(existingPid, 0) == 0 {
                kill(existingPid, SIGKILL)
            }
        }
        try? "\(myPid)".write(toFile: lockPath, atomically: true, encoding: .utf8)

        JarvisWidgetController.shared = self
        NSApp.setActivationPolicy(.accessory)
        setupStatusItem()
        setupWindow()
        registerHotKeys()
        
        // Start microphone and engage orange indicator
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            self.startMicrophone()
        }
    }
    
    func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem.button {
            button.title = "⚡"
            button.action = #selector(toggleWidget)
            button.target = self
        }
    }
    
    func setupWindow() {
        let screen = NSScreen.main?.visibleFrame ?? NSRect(x: 0, y: 0, width: 1440, height: 900)
        let width: CGFloat = 340
        let height: CGFloat = 440
        let rect = NSRect(x: screen.maxX - width - 24, y: screen.minY + 40, width: width, height: height)
        
        window = FloatingWidgetPanel(
            contentRect: rect,
            styleMask: [.borderless],
            backing: .buffered,
            defer: false
        )
        window.level = .floating
        window.isOpaque = false
        window.backgroundColor = .clear
        window.hasShadow = false
        window.isMovableByWindowBackground = true
        window.hidesOnDeactivate = false
        window.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary]
        
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "widget")
        config.websiteDataStore = WKWebsiteDataStore.nonPersistent()
        
        webView = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: height), configuration: config)
        webView.setValue(false, forKey: "drawsBackground")
        window.contentView = webView
        
        if let url = URL(string: "http://127.0.0.1:8080/widget?t=\(Date().timeIntervalSince1970)") {
            let req = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalAndRemoteCacheData, timeoutInterval: 10)
            webView.load(req)
        }
        
        window.makeKeyAndOrderFront(nil)
    }
    
    // MARK: - Native CoreAudio Microphone Engine (Orange Dot Controller)
    func startMicrophone() {
        guard !isAudioRecording else { return }
        let input = audioEngine.inputNode
        let bus = 0
        let srcFormat = input.outputFormat(forBus: bus)
        guard srcFormat.sampleRate > 0 else {
            print("[Void Native Mic] Invalid sample rate")
            return
        }
        
        guard let dstFormat = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: 16000, channels: 1, interleaved: true) else {
            return
        }
        self.converter = AVAudioConverter(from: srcFormat, to: dstFormat)
        
        input.removeTap(onBus: bus)
        
        audioLock.lock()
        speechPcmBuffer.removeAll()
        isUserSpeaking = false
        silenceStart = nil
        audioLock.unlock()
        
        input.installTap(onBus: bus, bufferSize: 1024, format: srcFormat) { [weak self] buffer, _ in
            self?.processAudioBuffer(buffer: buffer, srcFormat: srcFormat, dstFormat: dstFormat)
        }
        
        audioEngine.prepare()
        do {
            try audioEngine.start()
            isAudioRecording = true
            print("[Void Native Mic] AVAudioEngine online. Orange dot ON in menu bar.")
        } catch {
            print("[Void Native Mic Error] Engine start failed: \(error)")
        }
    }
    
    func stopMicrophone() {
        guard isAudioRecording else { return }
        let bus = 0
        audioEngine.inputNode.removeTap(onBus: bus)
        audioEngine.stop()
        isAudioRecording = false
        audioLock.lock()
        speechPcmBuffer.removeAll()
        isUserSpeaking = false
        silenceStart = nil
        audioLock.unlock()
        print("[Void Native Mic] AVAudioEngine offline. Orange dot OFF in menu bar.")
    }
    
    func processAudioBuffer(buffer: AVAudioPCMBuffer, srcFormat: AVAudioFormat, dstFormat: AVAudioFormat) {
        // 1. HARDWARE ACOUSTIC ECHO MUTE: Discard all microphone buffers while Void is speaking!
        if FileManager.default.fileExists(atPath: "/tmp/void_speaking.lock") {
            audioLock.lock()
            speechPcmBuffer.removeAll()
            isUserSpeaking = false
            silenceStart = nil
            audioLock.unlock()
            return
        }

        guard let floatData = buffer.floatChannelData?[0] else { return }
        let frameCount = Int(buffer.frameLength)
        if frameCount == 0 { return }
        
        var sum: Float = 0
        for i in 0..<frameCount {
            let sample = floatData[i]
            sum += sample * sample
        }
        let rms = sqrt(sum / Float(frameCount))
        
        let targetFrames = AVAudioFrameCount(Double(buffer.frameLength) * 16000.0 / srcFormat.sampleRate)
        guard let outBuffer = AVAudioPCMBuffer(pcmFormat: dstFormat, frameCapacity: targetFrames + 100),
              let converter = self.converter else { return }
        
        var error: NSError?
        let inputBlock: AVAudioConverterInputBlock = { _, outStatus in
            outStatus.pointee = .haveData
            return buffer
        }
        converter.convert(to: outBuffer, error: &error, withInputFrom: inputBlock)
        
        guard let int16Data = outBuffer.int16ChannelData?[0] else { return }
        let pcmChunk = Data(bytes: int16Data, count: Int(outBuffer.frameLength) * 2)
        
        audioLock.lock()
        defer { audioLock.unlock() }
        
        let now = Date().timeIntervalSince1970
        let speechThreshold: Float = 0.024 // Calibrated threshold for intentional user voice
        
        if rms > speechThreshold {
            if !isUserSpeaking {
                isUserSpeaking = true
                speechStartTime = now
                speechPcmBuffer.removeAll()
                print("\n[Void Native Mic] Speech detected (RMS: \(String(format: "%.4f", rms))). Buffering speech...")
            }
            speechPcmBuffer.append(pcmChunk)
            silenceStart = nil
        } else if isUserSpeaking {
            speechPcmBuffer.append(pcmChunk)
            if silenceStart == nil {
                silenceStart = now
            } else if now - silenceStart! >= 0.75 || now - speechStartTime >= 10.0 {
                let completedPcm = speechPcmBuffer
                speechPcmBuffer.removeAll()
                isUserSpeaking = false
                silenceStart = nil
                
                // If speech has sufficient length (> 0.45s), send for execution
                if completedPcm.count >= 16000 * 2 * 45 / 100 {
                    DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                        self?.sendVoiceCommand(pcmData: completedPcm)
                    }
                }
            }
        }
    }
    
    func sendVoiceCommand(pcmData: Data) {
        let wav = createWavData(from: pcmData, sampleRate: 16000, channels: 1)
        guard let url = URL(string: "http://127.0.0.1:8080/api/voice_command") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("audio/wav", forHTTPHeaderField: "Content-Type")
        request.httpBody = wav
        
        URLSession.shared.dataTask(with: request) { data, _, err in
            if let err = err {
                print("[Void Voice Send Error] \(err)")
            } else if let data = data, let str = String(data: data, encoding: .utf8) {
                print("[Void Voice Executed] \(str)")
            }
        }.resume()
    }
    
    // MARK: - Hotkey Configuration & Registration
    func loadConfig() -> HotKeyConfig {
        if let data = try? Data(contentsOf: URL(fileURLWithPath: configFile)),
           let cfg = try? JSONDecoder().decode(HotKeyConfig.self, from: data) {
            return cfg
        }
        // Default to Cmd + Shift + V (keyCode 9 for V, cmdKey | shiftKey)
        return HotKeyConfig(label: "⌘⇧V", keyCode: UInt32(kVK_ANSI_V), modifiers: UInt32(cmdKey | shiftKey))
    }
    
    func saveConfig(_ cfg: HotKeyConfig) {
        if let data = try? JSONEncoder().encode(cfg) {
            try? data.write(to: URL(fileURLWithPath: configFile))
        }
    }
    
    func registerHotKeys() {
        hotKeyRefs.forEach { UnregisterEventHotKey($0) }
        hotKeyRefs = []
        
        let cfg = loadConfig()
        
        // 1. Carbon Global Event Dispatcher (works across ALL apps system-wide)
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        InstallEventHandler(GetApplicationEventTarget(), { (_, _, _) -> OSStatus in
            DispatchQueue.main.async {
                JarvisWidgetController.shared?.toggleWidget()
            }
            return noErr
        }, 1, &eventType, nil, nil)
        
        // Register Command + Shift + V
        var userRef: EventHotKeyRef?
        if RegisterEventHotKey(cfg.keyCode, cfg.modifiers, EventHotKeyID(signature: OSType(0x564F4944), id: 1), GetApplicationEventTarget(), 0, &userRef) == noErr, let r = userRef {
            hotKeyRefs.append(r)
        }
        
        // Also register backup shortcut: Ctrl + Space
        var backup1: EventHotKeyRef?
        if RegisterEventHotKey(UInt32(kVK_Space), UInt32(controlKey), EventHotKeyID(signature: OSType(0x564F4944), id: 2), GetApplicationEventTarget(), 0, &backup1) == noErr, let r = backup1 {
            hotKeyRefs.append(r)
        }
        
        // 2. Cocoa NSEvent Global Key Monitor Fallback
        NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            if event.modifierFlags.contains([.command, .shift]) && (event.keyCode == 9 || event.keyCode == cfg.keyCode) {
                DispatchQueue.main.async {
                    JarvisWidgetController.shared?.toggleWidget()
                }
            }
        }
    }
    
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let dict = message.body as? [String: Any], let action = dict["action"] as? String else { return }
        
        if action == "focus" {
            DispatchQueue.main.async {
                NSApp.activate(ignoringOtherApps: true)
                self.window.makeKeyAndOrderFront(nil)
            }
        } else if action == "unfocus" {
            DispatchQueue.main.async {
                self.window.resignKey()
            }
        } else if action == "move", let dx = dict["dx"] as? Double, let dy = dict["dy"] as? Double {
            DispatchQueue.main.async {
                var origin = self.window.frame.origin
                origin.x += CGFloat(dx)
                origin.y -= CGFloat(dy)
                self.window.setFrameOrigin(origin)
            }
        } else if action == "sleep" || action == "close" {
            DispatchQueue.main.async {
                self.window.orderOut(nil)
                self.stopMicrophone()
                if let url = URL(string: "http://127.0.0.1:8080/api/sleep") {
                    URLSession.shared.dataTask(with: url).resume()
                }
            }
        } else if action == "shutdown" {
            DispatchQueue.main.async {
                self.stopMicrophone()
                self.window.orderOut(nil)
                NSApp.terminate(nil)
            }
        } else if action == "set_custom_hotkey",
                  let label = dict["label"] as? String,
                  let code = dict["keyCode"] as? UInt32,
                  let mods = dict["modifiers"] as? UInt32 {
            let newCfg = HotKeyConfig(label: label, keyCode: code, modifiers: mods)
            self.saveConfig(newCfg)
            DispatchQueue.main.async {
                self.registerHotKeys()
                self.webView.evaluateJavaScript("setHotkeyBadge('\(label)')", completionHandler: nil)
            }
        }
    }
    
    @objc func toggleWidget() {
        let now = Date().timeIntervalSince1970
        if now - lastToggleTime < 0.35 {
            return
        }
        lastToggleTime = now

        if window.isVisible {
            // CLOSING: Hide window & turn mic OFF (Orange dot OFF)
            window.orderOut(nil)
            stopMicrophone()
            if let url = URL(string: "http://127.0.0.1:8080/api/sleep") {
                URLSession.shared.dataTask(with: url).resume()
            }
        } else {
            // WAKING UP: Show window & turn mic ON (Orange dot ON)
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            startMicrophone()
            if let url = URL(string: "http://127.0.0.1:8080/api/wake_and_listen") {
                URLSession.shared.dataTask(with: url).resume()
            }
        }
    }
}

let app = NSApplication.shared
let delegate = JarvisWidgetController()
app.delegate = delegate
app.run()
