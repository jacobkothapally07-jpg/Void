import Cocoa
import WebKit

class FloatingWidgetPanel: NSPanel {
    override var canBecomeKey: Bool { return true }
    override var canBecomeMain: Bool { return true }
}

class JarvisWidgetController: NSObject, NSApplicationDelegate, WKScriptMessageHandler {
    var window: FloatingWidgetPanel!
    var webView: WKWebView!
    var statusItem: NSStatusItem!
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        setupStatusItem()
        setupWindow()
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
        let rect = NSRect(x: screen.maxX - width - 20, y: screen.minY + 40, width: width, height: height)
        
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
    
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let dict = message.body as? [String: Any], let action = dict["action"] as? String else { return }
        if action == "focus" {
            DispatchQueue.main.async {
                NSApp.activate(ignoringOtherApps: true)
                self.window.makeKeyAndOrderFront(nil)
            }
        }
    }
    
    @objc func toggleWidget() {
        if window.isVisible {
            window.orderOut(nil)
        } else {
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
        }
    }
}

let app = NSApplication.shared
let delegate = JarvisWidgetController()
app.delegate = delegate
app.run()
