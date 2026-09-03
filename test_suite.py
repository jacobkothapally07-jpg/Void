import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.system_tools import get_system_health, set_mac_volume
from tools.notification_tools import send_desktop_notification
from tools.utility_tools import get_current_time
from tools import TOOL_REGISTRY, TOOL_DEFINITIONS

print("=== TESTING JARVIS TOOL REGISTRY ===")
print(f"Registered tools count: {len(TOOL_REGISTRY)}")
assert len(TOOL_REGISTRY) == len(TOOL_DEFINITIONS)

print("\n--- 1. Testing System Health ---")
health = get_system_health()
print(health)
assert health["status"] == "success"
assert "cpu" in health
assert "memory" in health
assert "disk" in health

print("\n--- 2. Testing Utility Tools (Time) ---")
t = get_current_time()
print(t)
assert "current_date" in t and "current_time" in t

print("\n--- 3. Testing Desktop Notification ---")
notif = send_desktop_notification("JARVIS Diagnostics", "All core modules online, Sir.")
print(notif)
assert notif["status"] == "success"

print("\n=== ALL LOCAL TOOLS VERIFIED SUCCESSFULLY ===")
