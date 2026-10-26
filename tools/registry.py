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
from tools.sentry_tools import activate_sentry_mode, capture_sentry_frame as trigger_sentry_scan
from tools.email_tools import get_unread_emails, draft_email_reply
from tools.meeting_tools import generate_meeting_summary, save_to_apple_notes
from tools.file_tools import organize_folder, find_files_by_keyword
from tools.web_agent_tools import search_and_summarize
from tools.timer_tools import set_timer
from tools.spotify_tools import control_spotify
from tools.imessage_tools import send_imessage
from tools.math_tools import calculate_expression
from tools.file_reader_tool import read_workspace_file
from tools.coding_solver_tools import toggle_watch_screen, solve_and_paste_code, ask_about_screen
from tools.window_tools import arrange_window, type_into_active_app
from tools.meeting_copilot_tools import start_meeting_copilot, stop_meeting_copilot, record_meeting_point
from tools.dictation_tools import dictate_and_insert
from tools.screen_recording_tools import start_screen_recording, stop_screen_recording
from tools.memory_tools import remember_fact, recall_memory, forget_memory
from tools.autopilot_tools import pilot_youtube_search, pilot_summarize_screen_to_notes, pilot_git_commit

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
    "send_imessage": send_imessage,
    "control_spotify": control_spotify,
    "calculate_expression": calculate_expression,
    "read_workspace_file": read_workspace_file,
    "toggle_watch_screen": toggle_watch_screen,
    "solve_and_paste_code": solve_and_paste_code,
    "ask_about_screen": ask_about_screen,
    "arrange_window": arrange_window,
    "type_into_active_app": type_into_active_app,
    "start_meeting_copilot": start_meeting_copilot,
    "stop_meeting_copilot": stop_meeting_copilot,
    "record_meeting_point": record_meeting_point,
    "dictate_and_insert": dictate_and_insert,
    "start_screen_recording": start_screen_recording,
    "stop_screen_recording": stop_screen_recording,
    "remember_fact": remember_fact,
    "recall_memory": recall_memory,
    "forget_memory": forget_memory,
    "pilot_youtube_search": pilot_youtube_search,
    "pilot_summarize_screen_to_notes": pilot_summarize_screen_to_notes,
    "pilot_git_commit": pilot_git_commit,
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
    },
    {
        "name": "control_spotify",
        "description": "Controls Spotify playback natively on macOS. Actions: 'play', 'pause', 'toggle', 'next', 'previous', 'now_playing'. Optionally pass query for song search.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["play", "pause", "toggle", "next", "previous", "now_playing"], "description": "Playback control action."},
                "query": {"type": "string", "description": "Song, artist, or album to search and play if action is play."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "send_imessage",
        "description": "Sends an iMessage or SMS text to a contact or phone number via macOS Messages.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Contact name or phone number."},
                "message": {"type": "string", "description": "The exact message content."}
            },
            "required": ["recipient", "message"]
        }
    },
    {
        "name": "calculate_expression",
        "description": "Safely evaluates mathematical expressions, math calculations, algebra, square roots, trigonometry, powers, and logarithms.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical formula to calculate (e.g. 'sqrt(144) + 25 * 4', 'sin(pi/2)')."}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "read_workspace_file",
        "description": "Safely reads and inspects the contents of any text file, script, code file, or document on the user machine.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read."},
                "max_lines": {"type": "integer", "description": "Maximum lines to read (default: 200)."}
            },
            "required": ["path"]
        }
    },
    {
        "name": "toggle_watch_screen",
        "description": "Toggles continuous 'Watch My Screen' active monitoring mode. Keep active to give Jarvis real-time sight of your display.",
        "parameters": {
            "type": "object",
            "properties": {
                "active": {"type": "boolean", "description": "True to start watching screen, False to stop."}
            },
            "required": ["active"]
        }
    },
    {
        "name": "solve_and_paste_code",
        "description": "Scans the screen for coding questions, LeetCode problems, or programming tasks, writes optimal code, and automatically pastes it into the active code editor via Cmd+V.",
        "parameters": {
            "type": "object",
            "properties": {
                "auto_paste": {"type": "boolean", "description": "True to paste directly into the editor, False to copy only to clipboard."}
            },
            "required": []
        }
    },
    {
        "name": "ask_about_screen",
        "description": "Answers questions about whatever is currently visible on the user Mac screen, debugs compiler errors, or explains UI elements.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The specific question or prompt regarding what is on screen."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "arrange_window",
        "description": "Arranges, tiles, centers, or maximizes application windows on macOS displays.",
        "parameters": {
            "type": "object",
            "properties": {
                "preset": {"type": "string", "enum": ["left_half", "right_half", "maximize", "center"], "description": "Window position preset."},
                "app_name": {"type": "string", "description": "Target application name (empty for frontmost application)."}
            },
            "required": ["preset"]
        }
    },
    {
        "name": "dictate_and_insert",
        "description": "Polishes spoken speech into formatted text and types or pastes it directly at the active cursor on macOS.",
        "parameters": {
            "type": "object",
            "properties": {
                "raw_text": {"type": "string", "description": "The text or speech to clean up and insert."}
            },
            "required": ["raw_text"]
        }
    },
    {
        "name": "start_meeting_copilot",
        "description": "Starts Meeting Copilot to take structured notes, record discussion, and capture action items during video calls or meetings.",
        "parameters": {
            "type": "object",
            "properties": {
                "meeting_title": {"type": "string", "description": "Title or subject of the meeting."}
            },
            "required": []
        }
    },
    {
        "name": "stop_meeting_copilot",
        "description": "Concludes the active meeting and automatically writes the formatted minutes and action items to Apple Notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title for the saved Apple Note."}
            },
            "required": []
        }
    },
    {
        "name": "start_screen_recording",
        "description": "Starts high-definition screen video recording on macOS and saves directly to the Desktop.",
        "parameters": {
            "type": "object",
            "properties": {
                "duration_seconds": {"type": "integer", "description": "Optional recording duration in seconds before auto-stopping."}
            },
            "required": []
        }
    },
    {
        "name": "stop_screen_recording",
        "description": "Stops the active screen recording and reveals the saved video file in Finder.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "remember_fact",
        "description": "Logs a personal user preference, habit, fact, project, or instruction permanently into the Neural Memory Vault.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Subject or topic to remember, e.g. favorite drink, pet name, primary coding language."},
                "fact": {"type": "string", "description": "The exact fact or preference to remember."},
                "category": {"type": "string", "description": "Category: profile, preference, project, or general."}
            },
            "required": ["topic", "fact"]
        }
    },
    {
        "name": "recall_memory",
        "description": "Searches the Neural Memory Vault for stored facts, preferences, or personal background information.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Subject or keyword to recall."}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "forget_memory",
        "description": "Permanently deletes a previously remembered personal fact or preference from the Neural Memory Vault.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic or keyword of the memory to remove."}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "pilot_youtube_search",
        "description": "Hands-free Mac pilot: searches YouTube for any query/song and autoplays the top video result in the browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Song name, artist, or video topic to search and play."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "pilot_summarize_screen_to_notes",
        "description": "Hands-free Mac pilot: captures the active screen/document, summarizes it with executive bullets, and saves to Apple Notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "custom_title": {"type": "string", "description": "Optional custom title for the Apple Note."}
            },
            "required": []
        }
    },
    {
        "name": "pilot_git_commit",
        "description": "Hands-free Mac pilot: stages workspace changes, generates a clean git commit message, and commits.",
        "parameters": {
            "type": "object",
            "properties": {
                "custom_message": {"type": "string", "description": "Optional custom git commit message."},
                "push": {"type": "boolean", "description": "Whether to git push to remote origin main."}
            },
            "required": []
        }
    }
]
