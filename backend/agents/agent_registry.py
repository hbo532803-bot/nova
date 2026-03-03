from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.execution_agent import ExecutionAgent


class AgentRegistry:
    """
    Holds all available agents.
    """

    def __init__(self):
        self.agents = [
            AnalysisAgent(),
            ExecutionAgent(),
        ]

    def get_candidates(self, plan: dict):
        return [a for a in self.agents if a.can_handle(plan)]
