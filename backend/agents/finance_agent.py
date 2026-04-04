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

    def execute(self, plan: dict) -> dict:
        topic = self._topic(plan)
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "business": {
                "target_audience": f"SMBs actively searching for {topic}",
                "offer": f"Done-for-you {topic} growth landing page + follow-up automation",
                "pricing_idea": {
                    "setup_fee_usd": 1500,
                    "monthly_usd": 300,
                    "upsell": "lead qualification automation",
                },
                "monetization": "setup + recurring optimization retainer",
            },
            "score": 5,
            "success": True,
        }
