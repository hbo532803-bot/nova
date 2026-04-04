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

    def execute(self, plan: dict) -> dict:
        topic = self._topic(plan)
        cta = f"Book your {topic} growth plan"
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "marketing": {
                "positioning": f"Outcome-first messaging for {topic}",
                "cta_text": cta,
                "lead_strategy": [
                    "Lead magnet + instant form follow-up",
                    "Proof section with case-style outcomes",
                    "Retarget visitors who reached form section",
                ],
                "channels": ["SEO landing page", "local search", "short-form social proof"],
            },
            "score": 5,
            "success": True,
        }
