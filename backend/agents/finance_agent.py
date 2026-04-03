from backend.agents.base_agent import BaseAgent


class FinanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("FinanceAgent")
        self.capabilities = {"finance", "roi", "capital"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        # Finance agent proposes experiment creation/scaling (delegated to economic engine action).
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "score": 5,
            "success": True,
        }

