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
    
    let configFile = NSString(string: "~/.jarvis_hotkey.json").expandingTildeInPath
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        JarvisWidgetController.shared = self
        NSApp.setActivationPolicy(.accessory)
        setupStatusItem()
        setupWindow()
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
        
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "widget")
        
        webView = WKWebView(frame: NSRect(x: 0, y: 0, width: width, height: height), configuration: config)
        webView.setValue(false, forKey: "drawsBackground")
        window.contentView = webView
        
        if let url = URL(string: "http://127.0.0.1:8080/widget") {
            webView.load(URLRequest(url: url))
        }
        
        window.makeKeyAndOrderFront(nil)
    }
    
    func loadConfig() -> HotKeyConfig {
        if let data = try? Data(contentsOf: URL(fileURLWithPath: configFile)),
           let cfg = try? JSONDecoder().decode(HotKeyConfig.self, from: data) {
            return cfg
        }
        // Default to Cmd + Shift + J (keyCode 38 for J, cmdKey | shiftKey)
        return HotKeyConfig(label: "⌘⇧J", keyCode: UInt32(kVK_ANSI_J), modifiers: UInt32(cmdKey | shiftKey))
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
        InstallEventHandler(GetEventDispatcherTarget(), { (_, _, _) -> OSStatus in
            DispatchQueue.main.async {
                JarvisWidgetController.shared?.toggleWidget()
            }
            return noErr
        }, 1, &eventType, nil, nil)
        
        // Register Command + Shift + J
        var userRef: EventHotKeyRef?
        if RegisterEventHotKey(cfg.keyCode, cfg.modifiers, EventHotKeyID(signature: OSType(0x4A415256), id: 1), GetEventDispatcherTarget(), 0, &userRef) == noErr, let r = userRef {
            hotKeyRefs.append(r)
        }
        
        // Also register backup shortcut: Ctrl + Space
        var backup1: EventHotKeyRef?
        if RegisterEventHotKey(UInt32(kVK_Space), UInt32(controlKey), EventHotKeyID(signature: OSType(0x4A415256), id: 2), GetEventDispatcherTarget(), 0, &backup1) == noErr, let r = backup1 {
            hotKeyRefs.append(r)
        }
        
        // 2. Cocoa NSEvent Global Key Monitor Fallback
        NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { event in
            // Check for Command + Shift + J (keyCode 38)
            if event.modifierFlags.contains([.command, .shift]) && event.keyCode == 38 {
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
            }
        } else if action == "shutdown" {
            DispatchQueue.main.async {
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
        if window.isVisible {
            window.orderOut(nil)
            if let url = URL(string: "http://127.0.0.1:8080/api/sleep") {
                URLSession.shared.dataTask(with: url).resume()
            }
        } else {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            webView.evaluateJavaScript("focusInput()", completionHandler: nil)
            if let url = URL(string: "http://127.0.0.1:8080/api/wake") {
                URLSession.shared.dataTask(with: url).resume()
            }
        }
    }
}

let app = NSApplication.shared
let delegate = JarvisWidgetController()
app.delegate = delegate
app.run()
