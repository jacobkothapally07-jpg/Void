import Cocoa
import WebKit
import Carbon

class FloatingWidgetPanel: NSPanel {
    override var canBecomeKey: Bool { return true }
    override var canBecomeMain: Bool { return true }
}

struct HotKeyConfig: Codable {
    var label: String
    var keyCode: UInt32
    var modifiers: UInt32
}

class JarvisWidgetController: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    static var shared: JarvisWidgetController?
    
    var window: FloatingWidgetPanel!
    var webView: WKWebView!
    var statusItem: NSStatusItem!
    var hotKeyRefs: [EventHotKeyRef] = []
    var lastToggleTime: TimeInterval = 0
    
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
        setupDistributedNotifications()
        registerHotKeys()
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
    
    func setupDistributedNotifications() {
        DistributedNotificationCenter.default().addObserver(forName: NSNotification.Name("com.jk.void.show"), object: nil, queue: .main) { [weak self] _ in
            self?.showWidget()
        }
        DistributedNotificationCenter.default().addObserver(forName: NSNotification.Name("com.jk.void.hide"), object: nil, queue: .main) { [weak self] _ in
            self?.hideWidget()
        }
    }
    
    func showWidget() {
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    
    func hideWidget() {
        window.orderOut(nil)
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
        
        // Register Command + Shift + J (backward compatibility with Jarvis)
        var jarvisRef: EventHotKeyRef?
        if RegisterEventHotKey(UInt32(kVK_ANSI_J), UInt32(cmdKey | shiftKey), EventHotKeyID(signature: OSType(0x4A415256), id: 2), GetApplicationEventTarget(), 0, &jarvisRef) == noErr, let r = jarvisRef {
            hotKeyRefs.append(r)
        }
        
        // Also register backup shortcut: Ctrl + Space
        var backup1: EventHotKeyRef?
        if RegisterEventHotKey(UInt32(kVK_Space), UInt32(controlKey), EventHotKeyID(signature: OSType(0x564F4944), id: 3), GetApplicationEventTarget(), 0, &backup1) == noErr, let r = backup1 {
            hotKeyRefs.append(r)
        }
        
        // 2. Cocoa NSEvent Global Key Monitor Fallback
        NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            if event.modifierFlags.contains([.command, .shift]) && (event.keyCode == 9 || event.keyCode == 38 || event.keyCode == cfg.keyCode) {
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
                self.showWidget()
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
                self.hideWidget()
                if let url = URL(string: "http://127.0.0.1:8080/api/dismiss") {
                    URLSession.shared.dataTask(with: url).resume()
                }
            }
        } else if action == "wake" || action == "listen" {
            DispatchQueue.main.async {
                self.showWidget()
                if let url = URL(string: "http://127.0.0.1:8080/api/wake_and_listen") {
                    URLSession.shared.dataTask(with: url).resume()
                }
            }
        } else if action == "shutdown" {
            DispatchQueue.main.async {
                self.hideWidget()
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
            // CLOSING: Hide overlay window, put Void in background standby
            hideWidget()
            if let url = URL(string: "http://127.0.0.1:8080/api/dismiss") {
                URLSession.shared.dataTask(with: url).resume()
            }
        } else {
            // WAKING UP: Show window, greet user, and start active listening
            showWidget()
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
