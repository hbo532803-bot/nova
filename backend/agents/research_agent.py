from backend.agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResearchAgent")
        self.capabilities = {"research", "opportunity_discovery"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        # Propose opportunity discovery actions.
        return {
            "agent": self.name,
            "decision": {"actions": [{"type": "OPPORTUNITY_DISCOVER", "payload": {}}]},
            "type": "analysis",
            "score": 6,
            "success": True,
        }

