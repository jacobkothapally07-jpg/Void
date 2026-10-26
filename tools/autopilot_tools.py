import os
import subprocess
import urllib.request
import urllib.parse
import ssl
import re
import time
from config import GEMINI_API_KEY
from voice.sound_effects import play_hud_chirp, play_target_lock

def _get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def pilot_youtube_search(query: str) -> dict:
    """
    Searches YouTube for any topic, song, or creator, resolves the #1 top video result,
    and autoplays it immediately in the default browser.
    """
    clean_query = query.strip()
    if not clean_query:
        return {"status": "error", "message": "Search query cannot be empty, Sir."}
        
    play_hud_chirp()
    encoded = urllib.parse.quote(clean_query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    
    top_video_url = search_url
    try:
        req = urllib.request.Request(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=4.0, context=_get_ssl_context()) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            video_ids = re.findall(r'\"videoId\":\"([a-zA-Z0-9_-]{11})\"', html)
            unique_ids = list(dict.fromkeys(video_ids))
            if unique_ids:
                top_id = unique_ids[0]
                top_video_url = f"https://www.youtube.com/watch?v={top_id}&autoplay=1"
    except Exception:
        pass
        
    subprocess.run(["open", top_video_url], check=False)
    return {
        "status": "success",
        "query": clean_query,
        "url": top_video_url,
        "detail": f"Playing the top result for '{clean_query}' on YouTube, Sir."
    }

def pilot_summarize_screen_to_notes(custom_title: str = "") -> dict:
    """
    Captures the active screen or frontmost document, generates an executive summary
    via Gemini 3.1 Pro/Flash, and automatically creates a formatted note in Apple Notes.
    """
    play_target_lock()
    temp_img = "/tmp/jarvis_screen_doc.png"
    
    # 1. Capture screen
    try:
        subprocess.run(["screencapture", "-x", temp_img], check=True, timeout=3.0)
    except Exception as e:
        return {"status": "error", "message": f"Screen capture failed: {e}"}
        
    # 2. Analyze with Gemini Vision
    import base64
    with open(temp_img, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    prompt = (
        "You are J.A.R.V.I.S., an elite executive assistant. "
        "Analyze this document/screen. Identify the main topic, extract the key points, "
        "insights, decisions, or action items. Format as concise HTML bullet points. "
        "Use <h2> for the title and <ul><li> for bullets. Keep it under 200 words."
    )
    
    summary_html = "<h2>Screen Summary</h2><ul><li>Active workspace reviewed.</li></ul>"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                ]
            }],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400}
        }
        import json
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=12.0, context=_get_ssl_context()) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean markdown codeblocks
            raw_text = re.sub(r"```html|```", "", raw_text).strip()
            summary_html = raw_text
    except Exception as e:
        summary_html = f"<h2>Screen Intelligence</h2><p>Analysis error: {str(e)}</p>"
        
    # 3. Create note in Apple Notes via AppleScript
    title = custom_title.strip() if custom_title else f"Executive Brief — {time.strftime('%b %d, %I:%M %p')}"
    note_content = f"<div><h1>{title}</h1>{summary_html}</div>"
    
    applescript = f'''
    tell application "Notes"
        activate
        try
            set targetFolder to folder "Notes" of account "iCloud"
            make new note at targetFolder with properties {{body:"{note_content.replace('"', '\\"')}"}}
        on error
            make new note with properties {{body:"{note_content.replace('"', '\\"')}"}}
        end try
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript], check=False)
    
    return {
        "status": "success",
        "title": title,
        "detail": f"Screen summarized and new executive note created in Apple Notes: '{title}', Sir."
    }

def pilot_git_commit(custom_message: str = "", push: bool = False, repo_path: str = "") -> dict:
    """
    Automates repo staging, intelligent commit message generation, and git commit.
    """
    target_repo = repo_path.strip() if repo_path else "/Users/jacobkothapally/.gemini/antigravity/scratch/jarvis"
    
    # 1. Check status
    st_res = subprocess.run(["git", "-C", target_repo, "status", "-s"], capture_output=True, text=True)
    changes = st_res.stdout.strip()
    if not changes:
        return {"status": "success", "detail": "Repository working tree is completely clean, Sir. No changes to commit."}
        
    play_hud_chirp()
    # 2. Stage changes
    subprocess.run(["git", "-C", target_repo, "add", "-A"], check=True)
    
    # 3. Determine commit message
    if custom_message.strip():
        commit_msg = custom_message.strip()
    else:
        # Generate conventional commit message
        changed_files = [line[3:].strip() for line in changes.splitlines()][:5]
        files_str = ", ".join(changed_files)
        commit_msg = f"Update workspace components: {files_str}"
        
    # 4. Commit
    c_res = subprocess.run(["git", "-C", target_repo, "commit", "-m", commit_msg], capture_output=True, text=True)
    if c_res.returncode != 0:
        return {"status": "error", "message": f"Git commit failed: {c_res.stderr.strip()}"}
        
    pushed_str = ""
    if push:
        subprocess.run(["git", "-C", target_repo, "push", "origin", "main"], check=False)
        pushed_str = " and pushed to remote"
        
    return {
        "status": "success",
        "commit_message": commit_msg,
        "detail": f"All changes staged, committed ({commit_msg}){pushed_str}, Sir."
    }
