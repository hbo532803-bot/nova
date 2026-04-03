from backend.agents.base_agent import BaseAgent


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketingAgent")
        self.capabilities = {"marketing", "traffic"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        # Propose running an experiment to measure traffic/engagement signals.
        # If an experiment_id was provided by the command grammar, it will be in actions already.
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "score": 5,
            "success": True,
        }

