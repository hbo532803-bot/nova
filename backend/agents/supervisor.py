from backend.agents.agent_registry import AgentRegistry
from backend.agents.parallel_executor import ParallelAgentExecutor
from backend.agents.agent_voting import AgentVotingSystem
from backend.agents.agent_blacklist import AgentBlacklist

from backend.guards.cost_guard import CostGuard
from backend.guards.human_gate import HumanGate
from backend.guards.circuit_breaker import CircuitBreaker

from backend.system.kill_switch import KillSwitch


class SupervisorAgent:
    """
    Phase-4 FINAL Supervisor (Production-Ready)
    """

    def __init__(self):

        self.registry = AgentRegistry()
        self.parallel = ParallelAgentExecutor()
        self.voting = AgentVotingSystem()
        self.blacklist = AgentBlacklist()

        self.cost_guard = CostGuard(max_budget=100.0)
        self.human_gate = HumanGate()
        self.circuit = CircuitBreaker()
        self.kill_switch = KillSwitch()

    # -------------------------------------------------
    # MAIN HANDLER
    # -------------------------------------------------

    def handle(self, plan: dict) -> dict:

        # -----------------------------
        # GLOBAL SAFETY
        # -----------------------------

        self.kill_switch.check()
        self.human_gate.require_approval(plan)

        # Permission context protection
        if "_permission_context" not in plan:
            raise RuntimeError("Permission context missing (bypass blocked)")

        # -----------------------------
        # FIND CANDIDATE AGENTS
        # -----------------------------

        candidates = [
            a for a in self.registry.get_candidates(plan)
            if not self.blacklist.is_blocked(a)
        ]

        if not candidates:
            raise RuntimeError("No eligible agents")

        # -----------------------------
        # COST CONTROL
        # -----------------------------

        self.cost_guard.charge(cost=1.0)

        # -----------------------------
        # EXECUTION
        # -----------------------------

        if plan.get("autonomy_level") == "LIMITED_AUTONOMY":

            results = self.parallel.execute(candidates, plan)

            decision = self.voting.resolve(results)

        else:

            # pick highest trust agent
            agent = sorted(
                candidates,
                key=lambda a: a.trust_score,
                reverse=True
            )[0]

            decision = agent.execute(plan)

            decision["agent_trust"] = agent.trust_score
            decision["agent"] = agent.name

        # -----------------------------
        # CIRCUIT BREAKER
        # -----------------------------

        success = decision.get("success", False)

        self.circuit.record(success)

        # -----------------------------
        # TRUST ADJUSTMENT
        # -----------------------------

        for agent in candidates:

            if agent.name == decision.get("agent"):

                agent.adjust_trust(success)

                self.blacklist.evaluate(agent)

        # -----------------------------
        # PASSIVE TRUST DECAY
        # -----------------------------

        for agent in candidates:

            agent.trust_score = max(0, agent.trust_score - 0.2)

        # -----------------------------
        # RESULT
        # -----------------------------

        return {
            "decision": decision,
            "budget": self.cost_guard.status(),
            "blacklisted_agents": list(self.blacklist.blacklisted)
        }