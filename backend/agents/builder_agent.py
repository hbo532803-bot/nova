from backend.agents.base_agent import BaseAgent
import re


class BuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__("BuilderAgent")
        self.capabilities = {"build", "diff_apply"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def _topic(self, plan: dict) -> str:
        goal = str(plan.get("goal") or "").strip()
        goal = re.sub(r"^\s*run\s+mission\s+", "", goal, flags=re.IGNORECASE).strip()
        if ":" in goal:
            goal = goal.split(":", 1)[1].strip()
        goal = re.sub(r"\[(standard|premium|basic)\]", "", goal, flags=re.IGNORECASE).strip()
        return goal or "business service"

    def _context(self, plan: dict) -> dict:
        topic = self._topic(plan)
        low = topic.lower()
        niche = next((k for k in ("gym", "salon", "clinic", "dentist", "restaurant", "cafe", "spa", "real estate") if k in low), "local business")
        location_match = re.search(r"\b(in|at|near)\s+([a-zA-Z][a-zA-Z\\s]{2,30})", topic, flags=re.IGNORECASE)
        location = location_match.group(2).strip() if location_match else "your city"
        intent = "sales" if any(x in low for x in ("sale", "sell", "revenue", "book")) else "lead_gen"
        return {"topic": topic, "niche": niche, "location": location, "intent": intent}

    def execute(self, plan: dict) -> dict:
        ctx = self._context(plan)
        topic = ctx["topic"]
        headline = f"Get 25% More {ctx['niche'].title()} Leads in {ctx['location']} in 30 Days"
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "execution",
            "website": {
                "headline": headline,
                "subheadline": f"Conversion-focused {topic} experience built for trust, faster follow-up, and booked consultations.",
                "benefits": [
                    f"Localized messaging for {ctx['location']} search intent",
                    "Proof-led credibility section and objection handling FAQ",
                    "Lead capture + instant callback workflow to reduce drop-off",
                ],
                "sections": [
                    "Problem Awareness",
                    "Offer & Outcome",
                    "Proof & Competitor Comparison",
                    "Pricing Snapshot",
                    "Lead Form + Callback Promise",
                ],
                "customer_journey": ["awareness", "consideration", "trust", "conversion", "follow-up"],
                "cta_text": f"Book a {ctx['niche']} growth call for {ctx['location']}",
                "form_fields": ["name", "email", "phone", "goal"],
                "differentiation": f"Unlike template agencies, this {ctx['niche']} page includes local proof, clear offer math, and same-day follow-up trigger.",
            },
            "score": 5,
            "success": True,
        }
