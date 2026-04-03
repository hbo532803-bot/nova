from backend.agents.base_agent import BaseAgent


class BuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__("BuilderAgent")
        self.capabilities = {"build", "diff_apply"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        # Builder proposes safe no-op by default (real build playbooks come from ExperimentRunner playbooks).
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "execution",
            "score": 5,
            "success": True,
        }

