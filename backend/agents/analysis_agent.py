from backend.agents.base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnalysisAgent")

    def can_handle(self, plan: dict) -> bool:
        return "analyze" in plan.get("steps", [])

    def execute(self, plan: dict) -> dict:
        # Agents propose decisions/actions; they never execute system actions directly.
        goal = str(plan.get("goal", "")).lower()

        if "market" in goal:
            decision = {"action_type": "MARKET_SCAN", "reason": "Market-related command"}
        elif "experiment" in goal:
            decision = {"action_type": "EXPERIMENT_CREATE", "reason": "Experiment-related command"}
        else:
            decision = {"action_type": "REFLECTION_RECORD", "reason": "Default to learning/no-op"}

        return {
            "agent": self.name,
            "decision": decision,
            "type": "analysis",
            "score": 5,
            "success": True,
        }
