import Cocoa
import WebKit
import Carbon

class FloatingWidgetPanel: NSPanel {
    override var canBecomeKey: Bool { return true }
    override var canBecomeMain: Bool { return true }
}

class JarvisWidgetController: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    static var shared: JarvisWidgetController?
    
    var window: FloatingWidgetPanel!
    var webView: WKWebView!
    var statusItem: NSStatusItem!
    var hotKeyRef: EventHotKeyRef?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        JarvisWidgetController.shared = self
        NSApp.setActivationPolicy(.accessory)
        setupStatusItem()
        setupWindow()
        registerGlobalHotKey()
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
        let width: CGFloat = 330
        let height: CGFloat = 400
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
    
    func registerGlobalHotKey() {
        var eventType = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
        InstallEventHandler(GetApplicationEventTarget(), { (_, _, _) -> OSStatus in
            DispatchQueue.main.async {
                JarvisWidgetController.shared?.toggleWidget()
            }
            return noErr
        }, 1, &eventType, nil, nil)
        
        let hotKeyID = EventHotKeyID(signature: OSType(0x4A415256), id: 1) // "JARV"
        // Register Option + Space (keyCode 49 is Space)
        RegisterEventHotKey(UInt32(kVK_Space), UInt32(optionKey), hotKeyID, GetApplicationEventTarget(), 0, &hotKeyRef)
    }
    
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let dict = message.body as? [String: Any], let action = dict["action"] as? String else { return }
        
        if action == "focus" {
            DispatchQueue.main.async {
                NSApp.activate(ignoringOtherApps: true)
                self.window.makeKeyAndOrderFront(nil)
            }
        } else if action == "move", let dx = dict["dx"] as? Double, let dy = dict["dy"] as? Double {
            DispatchQueue.main.async {
                var origin = self.window.frame.origin
                origin.x += CGFloat(dx)
                origin.y -= CGFloat(dy) // Cocoa Y-axis is inverted relative to web screenY
                self.window.setFrameOrigin(origin)
            }
        }
    }
    
    @objc func toggleWidget() {
        if window.isVisible && window.isKeyWindow {
            window.orderOut(nil)
        } else {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            webView.evaluateJavaScript("focusInput()", completionHandler: nil)
        }
    }
}

let app = NSApplication.shared
let delegate = JarvisWidgetController()
app.delegate = delegate
app.run()
