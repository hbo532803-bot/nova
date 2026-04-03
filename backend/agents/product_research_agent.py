from backend.agents.base_agent import BaseAgent


class ProductResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("ProductResearchAgent")
        self.capabilities = {"product_research", "research", "opportunity_discovery", "pmf"}

    def can_handle(self, plan: dict) -> bool:
        required = set(plan.get("required_capabilities") or [])
        return not required or bool(self.capabilities & required)

    def execute(self, plan: dict) -> dict:
        # Propose discovery / PMF probe actions (still executed via spine).
        actions = plan.get("actions") or []
        return {"agent": self.name, "decision": {"actions": actions}, "type": "analysis", "score": 7, "success": True}

