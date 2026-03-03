from backend.agents.base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnalysisAgent")

    def can_handle(self, plan: dict) -> bool:
        return "analyze" in plan.get("steps", [])

    def execute(self, plan: dict) -> dict:
        return {
            "agent": self.name,
            "result": "Analysis completed",
            "success": True
        }
