from __future__ import annotations

from backend.agents.base_agent import BaseAgent


class SpecAgent(BaseAgent):
    """
    Spec-defined agent (created by AgentFactory).
    Behavior: propose the plan's actions; specialization is expressed via capabilities + scoring.
    """

    def __init__(self, name: str, capabilities: set[str]):
        super().__init__(name)
        self.capabilities = set(capabilities or set())

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        return {
            "agent": self.name,
            "decision": {"actions": plan.get("actions") or []},
            "type": "analysis",
            "score": 6,
            "success": True,
        }

