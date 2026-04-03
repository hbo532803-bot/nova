from backend.agents.base_agent import BaseAgent


class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExecutionAgent")

    def can_handle(self, plan: dict) -> bool:
        return "execute" in plan.get("steps", [])

    def execute(self, plan: dict) -> dict:
        # Agents propose an execution decision (which action to run); Supervisor triggers execution.
        actions = plan.get("actions") or []
        if actions:
            decision = {"actions": actions}
        else:
            # Fallback to a safe no-op execution action.
            decision = {"actions": [{"type": "REFLECTION_RECORD", "payload": {"note": "noop"}}]}
        return {
            "agent": self.name,
            "decision": decision,
            "type": "execution",
            "score": 5,
            "success": True,
        }
