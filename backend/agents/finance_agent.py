from backend.agents.base_agent import BaseAgent
import re


class FinanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("FinanceAgent")
        self.capabilities = {"finance", "roi", "capital"}

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
        location = location_match.group(2).strip() if location_match else "your market"
        if any(x in low for x in ("premium", "luxury", "high-end")):
            audience_type = "premium"
            multiplier = 1.35
        elif any(x in low for x in ("budget", "affordable", "cheap")):
            audience_type = "budget"
            multiplier = 0.75
        else:
            audience_type = "mass"
            multiplier = 1.0
        return {"topic": topic, "niche": niche, "location": location, "audience_type": audience_type, "multiplier": multiplier}

    def execute(self, plan: dict) -> dict:
        ctx = self._context(plan)
        topic = ctx["topic"]
        m = float(ctx["multiplier"])
        pricing = {
            "starter": {"setup_usd": int(900 * m), "monthly_usd": int(180 * m), "best_for": "budget tests"},
            "growth": {"setup_usd": int(1600 * m), "monthly_usd": int(350 * m), "best_for": "steady lead volume"},
            "scale": {"setup_usd": int(2800 * m), "monthly_usd": int(700 * m), "best_for": "multi-channel expansion"},
        }
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "business": {
                "target_audience": f"{ctx['audience_type'].title()}-intent {ctx['niche']} buyers in {ctx['location']}",
                "offer": f"Done-for-you {topic} acquisition funnel with local proof and callback automation",
                "pricing_idea": pricing,
                "pricing_sensitivity_logic": f"{ctx['audience_type']} segment pricing adjusted for {ctx['location']}",
                "monetization": "setup fee + monthly performance optimization retainer",
                "funnel_idea": "Ad/Search click -> proof-first landing page -> instant form + callback SLA -> offer consult close",
            },
            "score": 5,
            "success": True,
        }
