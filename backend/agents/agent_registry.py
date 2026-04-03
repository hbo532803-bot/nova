from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.execution_agent import ExecutionAgent
from backend.agents.research_agent import ResearchAgent
from backend.agents.builder_agent import BuilderAgent
from backend.agents.marketing_agent import MarketingAgent
from backend.agents.finance_agent import FinanceAgent
from backend.agents.product_research_agent import ProductResearchAgent
from backend.agents.system_builder_agent import SystemBuilderAgent
from backend.agents.growth_experiment_agent import GrowthExperimentAgent
from backend.agents.finance_strategy_agent import FinanceStrategyAgent
from backend.agents.spec_agent import SpecAgent
from backend.agents.capability_registry import CapabilityRegistry, CapabilityProfile
from backend.database import get_db
import json


class AgentRegistry:
    """
    Holds all available agents.
    """

    def __init__(self):
        self.agents = [
            AnalysisAgent(),
            ResearchAgent(),
            ProductResearchAgent(),
            MarketingAgent(),
            GrowthExperimentAgent(),
            FinanceAgent(),
            FinanceStrategyAgent(),
            BuilderAgent(),
            SystemBuilderAgent(),
            ExecutionAgent(),
        ]
        self._load_spec_agents()
        self.capabilities = CapabilityRegistry()

    def _load_spec_agents(self) -> None:
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key='agent_specs'")
                row = cursor.fetchone()
            if not row or not row["value"]:
                return
            specs = json.loads(str(row["value"]))
            if not isinstance(specs, list):
                return
            for s in specs:
                if bool(s.get("retired")):
                    continue
                name = str(s.get("name") or "").strip()
                caps = set(s.get("capabilities") or [])
                if name:
                    self.agents.append(SpecAgent(name, caps))
        except Exception:
            return

    def get_candidates(self, plan: dict):
        required = set(plan.get("required_capabilities") or [])
        candidates = []
        if required:
            profiles = [CapabilityProfile(agent_name=a.name, capabilities=set(a.capabilities or set())) for a in self.agents]
            ranked = self.capabilities.best(profiles, required)
            allowed_names = {p.agent_name for p, score in ranked if score > 0}
            for a in self.agents:
                if a.name in allowed_names:
                    candidates.append(a)
            return candidates

        for a in self.agents:
            if a.can_handle(plan):
                candidates.append(a)
        return candidates
