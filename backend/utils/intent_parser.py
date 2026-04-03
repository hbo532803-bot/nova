from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntentResult:
    intent: str
    service: str
    confidence: int


_INTENT_RULES: list[tuple[str, tuple[str, ...], str]] = [
    ("website_build", ("website", "landing page", "site", "web app"), "website_development"),
    ("lead_generation", ("lead", "prospect", "outreach", "pipeline"), "lead_generation"),
    ("automation", ("automation", "automate", "workflow", "zap", "integration"), "business_automation"),
    ("marketing", ("ads", "campaign", "seo", "social", "growth"), "marketing_growth"),
]


def parse_intent(user_text: str) -> IntentResult:
    text = (user_text or "").strip().lower()
    if not text:
        return IntentResult(intent="unknown", service="consultation", confidence=0)

    best_intent = "unknown"
    best_service = "consultation"
    best_hits = 0

    for intent, keywords, service in _INTENT_RULES:
        hits = sum(1 for k in keywords if k in text)
        if hits > best_hits:
            best_hits = hits
            best_intent = intent
            best_service = service

    if best_hits == 0:
        return IntentResult(intent="unknown", service="consultation", confidence=35)

    confidence = min(95, 55 + best_hits * 15)
    return IntentResult(intent=best_intent, service=best_service, confidence=confidence)
