from backend.agents.base_agent import BaseAgent
import re


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketingAgent")
        self.capabilities = {"marketing", "traffic"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def _topic(self, plan: dict) -> str:
        goal = str(plan.get("goal") or "").strip()
        goal = re.sub(r"^\s*run\s+mission\s+", "", goal, flags=re.IGNORECASE).strip()
        if ":" in goal:
            goal = goal.split(":", 1)[1].strip()
        goal = re.sub(r"\[(standard|premium|basic)\]", "", goal, flags=re.IGNORECASE).strip()
        return goal or "service business"

    def _context(self, plan: dict) -> dict:
        topic = self._topic(plan)
        low = topic.lower()
        niche = next((k for k in ("gym", "salon", "clinic", "dentist", "restaurant", "cafe", "spa", "real estate") if k in low), "local business")
        location_match = re.search(r"\b(in|at|near)\s+([a-zA-Z][a-zA-Z\\s]{2,30})", topic, flags=re.IGNORECASE)
        location = location_match.group(2).strip() if location_match else "your city"
        if any(x in low for x in ("premium", "luxury", "high-end")):
            segment = "premium"
        elif any(x in low for x in ("budget", "affordable", "cheap")):
            segment = "budget"
        else:
            segment = "mass"
        return {"topic": topic, "niche": niche, "location": location, "segment": segment}

    def execute(self, plan: dict) -> dict:
        ctx = self._context(plan)
        topic = ctx["topic"]
        cta = f"Claim your {ctx['location']} {ctx['niche']} growth audit"
        channels = ["local SEO", "Google Ads search intent", "Instagram ads"]
        if ctx["segment"] == "premium":
            channels = ["Instagram ads", "Google Ads high-intent", "influencer partnerships"]
        elif ctx["segment"] == "budget":
            channels = ["Google Maps + local SEO", "WhatsApp referral loops", "retargeting ads"]
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "marketing": {
                "positioning": f"Outcome-first messaging for {topic} with {ctx['segment']} segment hooks",
                "cta_text": cta,
                "lead_strategy": [
                    "Google/Instagram intent capture linked to localized landing page",
                    "Form completion -> instant SMS/WhatsApp callback workflow",
                    "Retarget drop-offs with offer-specific testimonials",
                ],
                "channels": channels,
                "differentiation": f"Compete on speed-to-response and transparent offer math instead of generic discounting in {ctx['location']}.",
            },
            "score": 5,
            "success": True,
        }
