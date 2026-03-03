import requests
from backend.frontend_api.event_bus import broadcast

ALLOWED_DOMAINS = [
    "api.github.com",
    "example.com"
]

def safe_get(url: str):
    domain = url.split("/")[2]

    if domain not in ALLOWED_DOMAINS:
        broadcast({
            "type": "log",
            "level": "warn",
            "message": f"Blocked external domain: {domain}"
        })
        return None

    try:
        r = requests.get(url, timeout=5)
        return r.text[:1000]
    except:
        return None
