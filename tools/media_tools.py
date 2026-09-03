import subprocess
import urllib.parse
import urllib.request
import re
import ssl

def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def play_media_on_internet(query: str, platform: str = "auto") -> dict:
    """
    Directly plays any music, song, video, movie trailer, podcast, or soundtrack.
    Directly fetches and starts the video with autoplay.
    """
    clean_query = query.strip()
    clean_platform = platform.lower().strip()
    
    # 1. Spotify
    if "spotify" in clean_platform or "spotify" in clean_query.lower():
        clean_q = re.sub(r"\b(on\s+spotify|spotify)\b", "", clean_query, flags=re.IGNORECASE).strip()
        spotify_uri = f"spotify:search:{urllib.parse.quote(clean_q)}"
        spotify_web = f"https://open.spotify.com/search/{urllib.parse.quote(clean_q)}"
        try:
            res = subprocess.run(["open", spotify_uri], capture_output=True)
            if res.returncode != 0:
                subprocess.run(["open", spotify_web], check=False)
        except Exception:
            subprocess.run(["open", spotify_web], check=False)
            
        return {
            "status": "success",
            "platform": "Spotify",
            "query": clean_q,
            "detail": f"Playing {clean_q} on Spotify."
        }

    # 2. YouTube Direct Video Auto-Play (Default)
    clean_q = re.sub(r"\b(on\s+youtube|youtube|video|play)\b", "", clean_query, flags=re.IGNORECASE).strip()
    encoded = urllib.parse.quote_plus(clean_q if clean_q else clean_query)
    search_url = f"https://www.youtube.com/results?search_query={encoded}"
    
    target_url = search_url
    try:
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=4, context=get_ssl_context()) as res:
            html = res.read().decode("utf-8")
            video_ids = re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", html)
            seen = set()
            unique_ids = [x for x in video_ids if not (x in seen or seen.add(x))]
            if unique_ids:
                target_url = f"https://www.youtube.com/watch?v={unique_ids[0]}&autoplay=1"
    except Exception:
        pass

    try:
        subprocess.run(["open", target_url], check=False)
        return {
            "status": "success",
            "platform": "YouTube",
            "query": clean_query,
            "url": target_url,
            "detail": f"Playing {clean_q or clean_query} for you now, Sir."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to play media: {str(e)}"}
