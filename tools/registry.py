from tools.system_tools import get_system_health, set_mac_volume, open_mac_application, control_mac_settings
from tools.notification_tools import send_desktop_notification, send_phone_notification
from tools.utility_tools import get_current_time, get_current_location, open_browser_url, launch_hud_server
from tools.communication_tools import send_text_message, make_phone_call
from tools.media_tools import play_media_on_internet
from tools.vision_tools import analyze_screen
from tools.protocol_tools import initiate_protocol
from tools.calendar_tools import create_reminder, get_today_schedule
from tools.productivity_tools import create_apple_note, manage_clipboard, schedule_calendar_event
from tools.terminal_tools import run_terminal_command
from tools.live_data_tools import get_live_weather, get_stock_price
from tools.security_tools import activate_sentry_mode, trigger_sentry_scan
from tools.email_tools import get_unread_emails, draft_email_reply
from tools.meeting_tools import generate_meeting_summary, save_to_apple_notes
from tools.file_tools import organize_folder, find_files_by_keyword
from tools.web_agent_tools import search_and_summarize
from tools.timer_tools import set_timer

TOOL_REGISTRY = {
    "get_system_health": get_system_health,
    "set_mac_volume": set_mac_volume,
    "open_mac_application": open_mac_application,
    "control_mac_settings": control_mac_settings,
    "send_desktop_notification": send_desktop_notification,
    "send_phone_notification": send_phone_notification,
    "get_current_time": get_current_time,
    "get_current_location": get_current_location,
    "open_browser_url": open_browser_url,
    "send_text_message": send_text_message,
    "make_phone_call": make_phone_call,
    "play_media_on_internet": play_media_on_internet,
    "analyze_screen": analyze_screen,
    "initiate_protocol": initiate_protocol,
    "set_timer": set_timer,
    "create_apple_note": create_apple_note,
    "manage_clipboard": manage_clipboard,
    "schedule_calendar_event": schedule_calendar_event,
    "run_terminal_command": run_terminal_command,
    "create_reminder": create_reminder,
    "get_today_schedule": get_today_schedule,
    "get_live_weather": get_live_weather,
    "get_stock_price": get_stock_price,
    "activate_sentry_mode": activate_sentry_mode,
    "trigger_sentry_scan": trigger_sentry_scan,
    "get_unread_emails": get_unread_emails,
    "draft_email_reply": draft_email_reply,
    "generate_meeting_summary": generate_meeting_summary,
    "save_to_apple_notes": save_to_apple_notes,
    "organize_folder": organize_folder,
    "find_files_by_keyword": find_files_by_keyword,
    "search_and_summarize": search_and_summarize
}

TOOL_DEFINITIONS = [
    {
        "name": "get_current_location",
        "description": "Detects the user exact real-time physical geographic location, city, region, coordinates, and country. Use when asked where am I, location, city, or coordinates.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_current_time",
        "description": "Returns the exact local time, date, day of week, and timezone. Use when asked for the time, date, day, or clock.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "set_timer",
        "description": "Sets a countdown timer for a given duration in seconds. Use whenever user asks for a timer, countdown, or timing an event.",
        "parameters": {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "Total duration in seconds."},
                "label": {"type": "string", "description": "Optional label."}
            },
            "required": ["duration_seconds"]
        }
    },
    {
        "name": "create_apple_note",
        "description": "Creates a new note directly inside Apple Notes with a title and content. Use whenever user asks to write a note, take notes, or save information.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the note."},
                "body": {"type": "string", "description": "Content / text of the note."}
            },
            "required": ["title", "body"]
        }
    },
    {
        "name": "manage_clipboard",
        "description": "Reads or writes to the macOS clipboard. Use to check what user copied or copy text for user.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "read to inspect copied text, write to copy text to clipboard."},
                "text": {"type": "string", "description": "Text to copy if action is write."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "control_mac_settings",
        "description": "Controls macOS hardware and system settings: lock (lock screen), dark_mode_toggle, dark_mode_on, dark_mode_off, empty_trash, sleep_display, take_screenshot.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Action: lock, sleep_display, dark_mode_toggle, dark_mode_on, dark_mode_off, empty_trash, take_screenshot"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "run_terminal_command",
        "description": "Executes shell / terminal commands on macOS (e.g. git, npm, python, disk space, brew, network diagnostics).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run."}
            },
            "required": ["command"]
        }
    },
    {
        "name": "schedule_calendar_event",
        "description": "Schedules an event directly on Apple Calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title or meeting name."},
                "start_time": {"type": "string", "description": "Time / date description."}
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_system_health",
        "description": "Checks MacBook battery level, power state, CPU utilization, RAM usage, and SSD storage. Use for battery, juice, storage, RAM, or laptop status.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "set_mac_volume",
        "description": "Sets the macOS master audio volume level (0 to 100).",
        "parameters": {
            "type": "object",
            "properties": {"level": {"type": "integer", "description": "Volume percentage from 0 to 100."}},
            "required": ["level"]
        }
    },
    {
        "name": "open_mac_application",
        "description": "Opens any Mac application (e.g. Safari, VS Code, Terminal, Spotify, Notion, Slack).",
        "parameters": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Name of the app to launch."}},
            "required": ["app_name"]
        }
    },
    {
        "name": "play_media_on_internet",
        "description": "Directly plays music, songs, tracks, artists, albums, or videos on YouTube or Spotify. DO NOT use for timers or reminders.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Song, artist, soundtrack or video to play."},
                "platform": {"type": "string", "description": "Platform (youtube, spotify, or auto)."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_screen",
        "description": "Takes a screenshot of the Mac display and visually analyzes open windows, code, errors, or documents.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to look for or analyze on screen."}},
            "required": []
        }
    },
    {
        "name": "get_live_weather",
        "description": "Retrieves real-time weather, temperature, humidity, and forecast for any city worldwide.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name, e.g. London, Hyderabad, New York."}},
            "required": ["city"]
        }
    },
    {
        "name": "get_stock_price",
        "description": "Retrieves live financial stock, crypto, or market pricing for any ticker (e.g. AAPL, TSLA, BTC).",
        "parameters": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "Stock or crypto symbol, e.g. AAPL, TSLA, BTC-USD."}},
            "required": ["symbol"]
        }
    },
    {
        "name": "create_reminder",
        "description": "Adds a task or reminder into native Apple Reminders.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Reminder text / task."},
                "due_date": {"type": "string", "description": "Optional due date or time."}
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_today_schedule",
        "description": "Reads today schedule and events from Apple Calendar.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "initiate_protocol",
        "description": "Executes workspace protocols: coding, study, meeting, clean house, or relax.",
        "parameters": {
            "type": "object",
            "properties": {"protocol_name": {"type": "string", "description": "Name of protocol (coding, study, meeting, clean house, relax)."}},
            "required": ["protocol_name"]
        }
    },
    {
        "name": "activate_sentry_mode",
        "description": "Arms MacBook sentry mode with FaceTime camera intruder alerts.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "organize_folder",
        "description": "Organizes a folder (e.g. ~/Downloads or ~/Desktop) into categorized subdirectories.",
        "parameters": {
            "type": "object",
            "properties": {"folder_path": {"type": "string", "description": "Path to organize, defaults to ~/Downloads."}},
            "required": []
        }
    },
    {
        "name": "find_files_by_keyword",
        "description": "Searches files across the Mac by name or content using Spotlight.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Keyword or file name to find."}},
            "required": ["query"]
        }
    },
    {
        "name": "get_unread_emails",
        "description": "Scans Apple Mail for unread and urgent messages.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "search_and_summarize",
        "description": "Searches the live web and retrieves up-to-date real-time 2026 facts, news, sports scores, releases, or research.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Web query or current event to search."}},
            "required": ["query"]
        }
    }
]
