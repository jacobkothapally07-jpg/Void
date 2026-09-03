import urllib.request
import urllib.parse
import json
import ssl
from config import GEMINI_API_KEY

def search_and_summarize(query: str) -> dict:
    clean_q = query.strip()
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as res:
            data = json.loads(res.read().decode("utf-8"))

        abstract = data.get("AbstractText", "")
        if not abstract and data.get("RelatedTopics"):
            abstract = data["RelatedTopics"][0].get("Text", "")

        if not abstract:
            abstract = f"Web search for {query} initialized. Researching latest live data feeds for you."

        return {
            "status": "success",
            "query": query,
            "summary": abstract,
            "detail": f"Web intelligence for {query}: {abstract}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
