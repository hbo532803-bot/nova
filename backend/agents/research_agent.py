from backend.agents.base_agent import BaseAgent
import re


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResearchAgent")
        self.capabilities = {"research", "opportunity_discovery"}

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
        location = location_match.group(2).strip() if location_match else "your local area"
        if any(x in low for x in ("premium", "luxury", "high-end")):
            audience_type = "premium"
        elif any(x in low for x in ("budget", "affordable", "cheap", "low cost")):
            audience_type = "budget"
        else:
            audience_type = "mass"
        if any(x in low for x in ("brand", "awareness", "positioning")):
            intent = "branding"
        elif any(x in low for x in ("sale", "sell", "revenue", "bookings")):
            intent = "sales"
        else:
            intent = "lead_gen"
        return {
            "niche": niche,
            "location": location,
            "audience_type": audience_type,
            "intent": intent,
            "topic": topic,
        }

    def execute(self, plan: dict) -> dict:
        ctx = self._context(plan)
        topic = ctx["topic"]
        niche = ctx["niche"]
        location = ctx["location"]
        problems = [
            f"{niche} buyers in {location} don't trust generic websites",
            f"{niche} prospects abandon when there is no clear offer and CTA",
            f"{niche} owners struggle to follow up leads quickly",
        ]
        angles = [
            f"proof-driven {niche} landing page for {location}",
            f"fast quote funnel for {niche}",
            f"{niche} authority positioning with testimonials",
        ]
        competitors = {
            "gym": ["cult.fit", "anytime fitness", "local boutique gyms"],
            "salon": ["urban company salons", "local premium salons", "home service beauticians"],
            "clinic": ["practo-listed clinics", "nearby multispecialty centers", "telehealth apps"],
            "dentist": ["clove dental", "nearby dental chains", "independent practitioners"],
        }.get(niche, ["nearby established providers", "aggregator marketplaces", "price-led freelancers"])
        return {
            "agent": self.name,
            "decision": {"actions": [{"type": "OPPORTUNITY_DISCOVER", "payload": {}}]},
            "type": "analysis",
            "research": {
                "topic": topic,
                "context": ctx,
                "problems": problems,
                "angles": angles,
                "keywords": [w for w in topic.lower().split() if len(w) > 2],
                "competitors": competitors,
                "differentiation": f"Outcome-based {niche} positioning for {location} with transparent offer + rapid follow-up.",
            },
            "score": 6,
            "success": True,
        }
