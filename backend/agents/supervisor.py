from backend.agents.agent_registry import AgentRegistry
from backend.agents.parallel_executor import ParallelAgentExecutor
from backend.agents.agent_voting import AgentVoting
from backend.agents.agent_blacklist import AgentBlacklist

from backend.guards.cost_guard import CostGuard
from backend.guards.human_gate import HumanGate
from backend.guards.circuit_breaker import CircuitBreaker
from backend.system.kill_switch import KillSwitch
from backend.execution.hardened_executor import hardened_execute

class SupervisorAgent:
    """
    Phase-4 FINAL Supervisor (Production-Ready)
    """

    def __init__(self):
        self.registry = AgentRegistry()
        self.parallel = ParallelAgentExecutor()
        self.voting = AgentVoting()
        self.blacklist = AgentBlacklist()

        self.cost_guard = CostGuard(max_budget=100.0)
        self.human_gate = HumanGate()
        self.circuit = CircuitBreaker()
        self.kill_switch = KillSwitch()

    def handle(self, plan: dict) -> dict:
        # 🔥 Global safety
        self.kill_switch.check()
        self.human_gate.require_approval(plan)

        candidates = [
            a for a in self.registry.get_candidates(plan)
            if not self.blacklist.is_blocked(a)
        ]

        if not candidates:
            raise RuntimeError("No eligible agents")

        # cost charge (flat demo cost)
        self.cost_guard.charge(cost=1.0)

        # execution
        if plan.get("autonomy_level") == "LIMITED_AUTONOMY":
            results = self.parallel.execute(candidates, plan)
            decision = self.voting.resolve(results)
        else:
            agent = sorted(candidates, key=lambda a: a.trust_score, reverse=True)[0]
            decision = agent.execute(plan)
            decision["agent_trust"] = agent.trust_score

        success = decision.get("success", False)
        self.circuit.record(success)

        for agent in candidates:
            if agent.name == decision.get("agent"):
                agent.adjust_trust(success)
                self.blacklist.evaluate(agent)
                 # --- PATCH START (ensure permission context present) ---
        if "_permission_context" not in plan:
         raise RuntimeError("Permission context missing (bypass blocked)")
# --- PATCH END ---
        # --- Agent passive decay ---
        for agent in candidates:
         agent.trust_score = max(0, agent.trust_score - 0.2)

        return {
            "decision": decision,
            "budget": self.cost_guard.status(),
            "blacklisted_agents": list(self.blacklist.blacklisted)
        }
       