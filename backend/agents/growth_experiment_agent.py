from backend.agents.base_agent import BaseAgent


class GrowthExperimentAgent(BaseAgent):
    def __init__(self):
        super().__init__("GrowthExperimentAgent")
        self.capabilities = {"growth_experimentation", "marketing", "traffic", "engagement", "conversions"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        actions = plan.get("actions") or []
        return {"agent": self.name, "decision": {"actions": actions}, "type": "analysis", "score": 7, "success": True}

