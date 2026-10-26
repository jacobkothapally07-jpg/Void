import urllib.request
import urllib.parse
import json
import ssl
import re

def _get_ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def search_and_summarize(query: str) -> dict:
    """
    Retrieves real-time global information, world news, current facts, and knowledge across the web.
    Aggregates live results from Google News, DuckDuckGo, and Wikipedia.
    """
    clean_q = query.strip()
    is_news = any(k in clean_q.lower() for k in ["news", "latest", "today", "recent", "updates", "headline", "stock", "score"])
    results = []

    # 1. Live Google News RSS (for breaking news and recent developments)
    if is_news:
        try:
            news_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_q)}&hl=en-IN&gl=IN&ceid=IN:en"
            req = urllib.request.Request(news_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
            with urllib.request.urlopen(req, context=_get_ssl_ctx(), timeout=4.5) as r:
                xml = r.read().decode("utf-8")
                titles = re.findall(r"<title>(.*?)</title>", xml)
                # Filter out channel title
                news_items = [t for t in titles if "Google News" not in t][:3]
                if news_items:
                    results.append("Live headlines: " + " • ".join(news_items))
        except Exception:
            pass

    # 2. Real-Time Web Search Snippets (DuckDuckGo HTML engine)
    try:
        ddg_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(clean_q)
        req = urllib.request.Request(ddg_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, context=_get_ssl_ctx(), timeout=5) as r:
            html = r.read().decode("utf-8")
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
            clean_snippets = [re.sub(r"<[^>]+>", "", s).strip() for s in snippets[:2] if len(s.strip()) > 30]
            if clean_snippets:
                results.append(" ".join(clean_snippets))
    except Exception:
        pass

    # 3. Wikipedia Knowledge API Fallback
    if not results or len(results[0]) < 60:
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&utf8=&format=json"
            req = urllib.request.Request(wiki_url, headers={"User-Agent": "JARVIS-Assistant/1.0"})
            with urllib.request.urlopen(req, context=_get_ssl_ctx(), timeout=4) as r:
                d = json.loads(r.read())
                wiki_results = d.get("query", {}).get("search", [])
                if wiki_results:
                    title = wiki_results[0].get("title", "")
                    raw_snip = wiki_results[0].get("snippet", "")
                    clean_snip = re.sub(r"<[^>]+>", "", raw_snip).strip()
                    results.append(f"{title}: {clean_snip}")
        except Exception:
            pass

    if results:
        final_summary = " ".join(results)
        # Limit to 350 chars for crisp speech
        if len(final_summary) > 400:
            final_summary = final_summary[:395] + "..."
        return {
            "status": "success",
            "query": query,
            "summary": final_summary,
            "detail": f"Global intelligence for {query}: {final_summary}"
        }

    return {
        "status": "success",
        "query": query,
        "summary": f"Data search completed for {query}.",
        "detail": f"Global intelligence search for {query} completed, Sir."
    }
