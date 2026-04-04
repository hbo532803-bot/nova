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

    def execute(self, plan: dict) -> dict:
        topic = self._topic(plan)
        headline = f"Get More Qualified {topic} Leads in 30 Days"
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "execution",
            "website": {
                "headline": headline,
                "subheadline": f"Conversion-focused {topic} website built for trust, speed, and booked calls.",
                "benefits": [
                    "Clear offer and outcome framing",
                    "Trust section with proof and FAQ",
                    "Lead capture form with instant follow-up trigger",
                ],
                "sections": ["Hero", "Benefits", "Process", "Proof", "FAQ", "Lead Form"],
                "cta_text": f"Start your {topic} growth plan",
                "form_fields": ["name", "email", "phone", "goal"],
            },
            "score": 5,
            "success": True,
        }
