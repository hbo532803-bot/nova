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

    def execute(self, plan: dict) -> dict:
        topic = self._topic(plan)
        problems = [
            f"{topic} buyers don't trust generic websites",
            f"{topic} prospects abandon when there is no clear offer and CTA",
            f"{topic} owners struggle to follow up leads quickly",
        ]
        angles = [
            f"proof-driven {topic} landing page",
            f"fast quote funnel for {topic}",
            f"{topic} authority positioning with testimonials",
        ]
        return {
            "agent": self.name,
            "decision": {"actions": [{"type": "OPPORTUNITY_DISCOVER", "payload": {}}]},
            "type": "analysis",
            "research": {
                "topic": topic,
                "problems": problems,
                "angles": angles,
                "keywords": [w for w in topic.lower().split() if len(w) > 2],
            },
            "score": 6,
            "success": True,
        }
