from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from backend.frontend_api.event_bus import broadcast

# Defaults are intentionally small; override with env vars in production.
DEFAULT_ALLOWLIST = {"api.github.com", "news.ycombinator.com", "www.producthunt.com", "trends.google.com", "www.reddit.com"}

# In-memory rate limiter (best-effort). Keys are domains.
_LAST_FETCH_AT: dict[str, float] = {}


def _allowlist() -> set[str]:
    raw = (os.getenv("NOVA_WEB_ALLOWLIST") or "").strip()
    if not raw:
        return set(DEFAULT_ALLOWLIST)
    return {d.strip().lower() for d in raw.split(",") if d.strip()}


def _min_interval_sec() -> float:
    try:
        return float(os.getenv("NOVA_WEB_MIN_INTERVAL_SEC") or 1.0)
    except Exception:
        return 1.0


def _is_allowed(domain: str) -> bool:
    return domain.lower() in _allowlist()


def _rate_limit(domain: str) -> None:
    now = time.time()
    min_int = _min_interval_sec()
    last = _LAST_FETCH_AT.get(domain, 0.0)
    if (now - last) < min_int:
        raise RuntimeError(f"rate_limited:{domain}")
    _LAST_FETCH_AT[domain] = now


def _extract_html_structures(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""

    meta: Dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        content = tag.get("content")
        if name and content and len(meta) < 30:
            meta[str(name).strip()] = str(content).strip()

    links: List[str] = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and isinstance(href, str):
            links.append(href)
        if len(links) >= 50:
            break

    # Lightweight text extract (bounded)
    text = soup.get_text(" ", strip=True)
    if len(text) > 2000:
        text = text[:2000]

    return {"title": title, "meta": meta, "links": links, "text": text}


def safe_get(url: str) -> Dict[str, Any]:
    """
    Safe WEB_GET:
    - domain allowlist
    - simple per-domain rate limiting
    - structured HTML parsing + metadata extraction
    - bounded outputs for playbooks
    """
    parsed = urlparse(url)
    domain = (parsed.netloc or "").lower()
    if not domain:
        return {"ok": False, "error": "invalid_url", "url": url}

    if not _is_allowed(domain):
        broadcast({"type": "log", "level": "warn", "message": f"Blocked external domain: {domain}"})
        return {"ok": False, "blocked": True, "reason": "domain_not_allowlisted", "domain": domain, "url": url}

    try:
        _rate_limit(domain)
        r = requests.get(
            url,
            timeout=5,
            headers={"User-Agent": "NovaBot/1.0 (safe_get)"},
        )
        content_type = str(r.headers.get("content-type") or "")
        body = r.text or ""
        body_snippet = body[:5000]

        out: Dict[str, Any] = {
            "ok": True,
            "url": url,
            "domain": domain,
            "status_code": int(r.status_code),
            "content_type": content_type,
            "headers": {
                "content-type": content_type,
                "cache-control": str(r.headers.get("cache-control") or ""),
            },
            "body_snippet": body_snippet,
        }

        if "html" in content_type.lower():
            out["html"] = _extract_html_structures(body)

        return out

    except Exception as e:
        return {"ok": False, "url": url, "domain": domain, "error": str(e)}
