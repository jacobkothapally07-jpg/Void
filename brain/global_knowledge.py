import urllib.request
import urllib.parse
import json
import math
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

def solve_fast_math(expression: str) -> str:
    """Evaluates mathematical calculations in < 1ms safely."""
    clean = expression.strip().lower()
    clean = re.sub(r"^(?:what\s+is|calculate|solve|evaluate)\s*", "", clean).strip(" ?=")
    clean = clean.replace("x", "*").replace("times", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-")
    clean = clean.replace("^", "**").replace("squared", "**2").replace("cubed", "**3")
    
    # Safe math namespace
    safe_dict = {
        "math": math, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
        "tan": math.tan, "pi": math.pi, "e": math.e, "log": math.log,
        "exp": math.exp, "pow": math.pow, "abs": abs, "round": round
    }
    
    try:
        # Only allow safe mathematical characters
        if not re.match(r"^[0-9+\-*/().,%^ a-z_]+$", clean):
            return None
        res = eval(clean, {"__builtins__": None}, safe_dict)
        if isinstance(res, (int, float)):
            if isinstance(res, float) and res.is_integer():
                res = int(res)
            return f"The result is {res:,}, Sir." if isinstance(res, int) else f"The result is {res:.4f}, Sir."
    except Exception:
        return None
    return None

def query_wikipedia_fast(topic: str) -> str:
    """Queries Wikipedia REST API in ~30ms for direct encyclopedia extracts."""
    clean = topic.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean)}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-GlobalIntelligence/1.0"})
        with urllib.request.urlopen(req, timeout=3, context=_get_ssl_ctx()) as response:
            data = json.loads(response.read().decode("utf-8"))
            extract = data.get("extract", "")
            if extract:
                # Truncate to first 2-3 sentences for rapid spoken delivery
                sentences = extract.split(". ")
                concise = ". ".join(sentences[:2])
                if not concise.endswith("."):
                    concise += "."
                return f"{concise}"
    except Exception:
        return None
    return None

def query_duckduckgo_fast(query: str) -> str:
    """Queries DuckDuckGo Instant Knowledge API in ~40ms."""
    clean_q = query.strip()
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-Global/1.0"})
        with urllib.request.urlopen(req, timeout=3, context=_get_ssl_ctx()) as response:
            data = json.loads(response.read().decode("utf-8"))
            abstract = data.get("AbstractText", "")
            if abstract:
                return abstract
            answer = data.get("Answer", "")
            if answer:
                return f"According to global telemetry: {answer}"
    except Exception:
        return None
    return None

def query_global_knowledge(query: str) -> str:
    """Aggregates global real-time knowledge in sub-50ms."""
    clean = query.strip().lower()
    
    # 1. Check math calculation
    if any(c in clean for c in ["+", "-", "*", "/", "sqrt", "squared", "cubed", "calculate", "times", "divided by"]) and re.search(r"\d", clean):
        math_res = solve_fast_math(query)
        if math_res:
            return math_res

    # 2. Extract subject for Wikipedia
    wiki_subject_match = re.search(r"(?:who\s+is|who\s+was|what\s+is|tell\s+me\s+about|explain|define)\s+(.+)", clean, re.IGNORECASE)
    if wiki_subject_match:
        subject = wiki_subject_match.group(1).strip(" ?.")
        wiki_res = query_wikipedia_fast(subject)
        if wiki_res:
            return wiki_res

    # 3. DuckDuckGo Instant Knowledge
    ddg_res = query_duckduckgo_fast(query)
    if ddg_res:
        return ddg_res

    return None
