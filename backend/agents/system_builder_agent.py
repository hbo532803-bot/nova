from backend.agents.base_agent import BaseAgent


class SystemBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__("SystemBuilderAgent")
        self.capabilities = {"system_building", "build", "diff_apply", "prototype"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        actions = plan.get("actions") or []
        return {"agent": self.name, "decision": {"actions": actions}, "type": "execution", "score": 6, "success": True}

