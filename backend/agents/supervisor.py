import logging
from backend.agents.agent_registry import AgentRegistry
from backend.agents.parallel_executor import ParallelAgentExecutor
from backend.agents.agent_voting import AgentVotingSystem
from backend.agents.agent_blacklist import AgentBlacklist

from backend.guards.cost_guard import CostGuard
from backend.guards.human_gate import HumanGate
from backend.guards.circuit_breaker import CircuitBreaker

from backend.system.kill_switch import KillSwitch
from backend.execution.execution_engine import ExecutionEngine
from backend.database import get_db
import datetime
from backend.execution.hardened_executor import hardened_execute
from backend.agents.collaboration import CollaborationOrchestrator
from backend.runtime.task_graph_engine import TaskGraphEngine
from backend.memory.working_memory import WorkingMemoryStore
from backend.db_retry import run_db_write_with_retry


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
        self.exec_engine = ExecutionEngine()
        self.collab = CollaborationOrchestrator()
        self.task_graph = TaskGraphEngine(max_parallel=3)
        self.working_memory = WorkingMemoryStore()

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

        # Shared team context for collaboration (intermediate result sharing)
        shared_context = plan.get("shared_context") or {}
        plan["shared_context"] = shared_context

        mission_id = str(plan.get("mission_id") or plan.get("created_at") or "")
        plan["mission_id"] = mission_id
        try:
            # Seed shared_context with recent mission memory (structured shared mission intelligence)
            plan["shared_context"]["mission_memory"] = self.working_memory.list(mission_id, limit=50)
        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in supervisor.py")

        # Task graph missions (complex multi-node execution)
        if isinstance(plan.get("task_graph"), dict):
            return self._handle_task_graph(plan)

        # If this plan contains multiple actions, run collaboration orchestration:
        if isinstance(plan.get("actions"), list) and len(plan.get("actions")) > 1:
            return self._handle_team_plan(plan)

        candidates = [a for a in self.registry.get_candidates(plan) if not self.blacklist.is_blocked(a)]

        if not candidates:
            # Capability gap handling (no bypass): create a spec-agent via action spine, then retry.
            required = list(plan.get("required_capabilities") or [])
            if required:
                create_plan = {
                    **plan,
                    "steps": ["execute"],
                    "actions": [
                        {
                            "type": "AGENT_FACTORY_CREATE",
                            "payload": {"required_capabilities": required, "mission_id": plan.get("mission_id")},
                            "assumed_failure": "agent_factory_create_fails",
                            "failure_impact": "capability_gap_persists",
                        }
                    ],
                }
                try:
                    hardened_execute(create_plan)
                    # refresh registry after spec insertion
                    self.registry = AgentRegistry()
                    candidates = [a for a in self.registry.get_candidates(plan) if not self.blacklist.is_blocked(a)]
                except Exception:
                    logging.getLogger(__name__).exception("Suppressed exception in supervisor.py")

            if not candidates:
                raise RuntimeError("No eligible agents")

        # -----------------------------
        # COST CONTROL
        # -----------------------------

        self.cost_guard.charge(cost=1.0)

        # -----------------------------
        # EXECUTION
        # -----------------------------

        chosen_agent_name = None

        if plan.get("autonomy_level") == "LIMITED_AUTONOMY":

            results = self.parallel.execute(candidates, plan)

            decision = self.voting.resolve(results)
            chosen_agent_name = decision.get("agent")

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
            chosen_agent_name = agent.name

        # -----------------------------
        # EXECUTE DECIDED ACTIONS (ONLY VIA EXECUTION ENGINE)
        # -----------------------------

        selected = decision.get("decision") if isinstance(decision, dict) else None
        if isinstance(selected, dict) and selected.get("actions"):
            exec_plan = {**plan, "actions": selected["actions"], "steps": ["execute"]}
            execution_result = hardened_execute(exec_plan)
        elif isinstance(plan.get("actions"), list) and plan.get("actions"):
            execution_result = hardened_execute(plan)
        else:
            execution_result = {"success": True, "data": {"info": "no actions to execute"}}

        decision["execution_result"] = execution_result
        decision["success"] = bool(execution_result.get("success"))

        # Record agent productivity outcome (persisted via ExecutionEngine; no bypass).
        if chosen_agent_name:
            self._record_agent_outcome(chosen_agent_name, bool(decision["success"]))

        # -----------------------------
        # AGENT LIFECYCLE STATE UPDATE
        # -----------------------------

        if chosen_agent_name:
            self._update_agent_state(chosen_agent_name, "IDLE")
            self._hibernate_if_inactive(hours=6)

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

    def _record_agent_outcome(self, agent_name: str, success: bool) -> None:
        exec_plan = {
            "goal": f"record agent handled_plan {agent_name}",
            "steps": ["execute"],
            "autonomy_level": "LIMITED_AUTONOMY",
            "_permission_context": "supervisor_agent",
            "assumed_failure": "agent_actions_insert_fails",
            "failure_impact": "productivity_signal_lost",
            "confidence_score": 80,
        }

        def action(_p):
            def _write(conn):
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO agent_actions (agent_name, action, result) VALUES (?, ?, ?)",
                    (agent_name, "handled_plan", "success" if success else "failure"),
                )
                conn.commit()
                return None

            run_db_write_with_retry("agent_actions.insert.handled_plan", _write)
            return {"agent": agent_name, "success": success}

        self.exec_engine.execute(exec_plan, action, rollback=lambda _p: None)

    def _handle_team_plan(self, plan: dict) -> dict:
        """
        Multi-step collaboration handler:
        - decompose actions into tasks
        - assign best-fit agents per task (capability matching)
        - share intermediate results via shared_context
        - execute each task's action slice via ExecutionEngine
        """
        tasks = self.collab.decompose(plan)
        team_log = []
        overall_success = True

        for t in tasks:
            subplan = {**plan, "actions": t.actions, "required_capabilities": t.required_capabilities, "steps": ["execute"]}
            candidates = [a for a in self.registry.get_candidates(subplan) if not self.blacklist.is_blocked(a)]
            if not candidates:
                team_log.append({"task": t.name, "error": "no_candidates"})
                overall_success = False
                continue

            # Choose highest trust among candidates for this task
            agent = sorted(candidates, key=lambda a: a.trust_score, reverse=True)[0]
            self._update_agent_state(agent.name, "BUSY")

            proposal = agent.execute(subplan)
            self.collab.share(plan["shared_context"], f"task:{t.name}:proposal", proposal, mission_id=plan.get("mission_id"))

            # Execute the subplan actions (no bypass)
            exec_result = hardened_execute(subplan)
            team_log.append({"task": t.name, "agent": agent.name, "proposal": proposal, "execution": exec_result})

            success = bool(exec_result.get("success"))
            overall_success = overall_success and success
            self._update_agent_state(agent.name, "IDLE")

        return {
            "decision": {
                "agent": "SupervisorTeam",
                "success": overall_success,
                "team_log": team_log,
            },
            "budget": self.cost_guard.status(),
            "blacklisted_agents": list(self.blacklist.blacklisted),
        }

    def _handle_task_graph(self, plan: dict) -> dict:
        graph = plan.get("task_graph") or {}
        mission_id = str(plan.get("mission_id") or "")

        def run_node(node):
            subplan = {
                **plan,
                "goal": f"{plan.get('goal')} :: node {node.id} {node.name}",
                "steps": ["execute"],
                "required_capabilities": node.required_capabilities,
                "actions": node.actions,
                "shared_context": plan.get("shared_context") or {},
                "mission_id": mission_id,
            }

            candidates = [a for a in self.registry.get_candidates(subplan) if not self.blacklist.is_blocked(a)]
            if not candidates:
                raise RuntimeError("no_candidates")
            agent = sorted(candidates, key=lambda a: a.trust_score, reverse=True)[0]
            self._update_agent_state(agent.name, "BUSY")

            proposal = agent.execute(subplan)
            self.collab.share(subplan["shared_context"], f"node:{node.id}:proposal", proposal, mission_id=mission_id)

            exec_result = hardened_execute(subplan)
            self.working_memory.put(mission_id, f"node:{node.id}:execution", str(exec_result))

            self._update_agent_state(agent.name, "IDLE")
            return {"agent": agent.name, "proposal": proposal, "execution": exec_result}

        result = self.task_graph.run(graph, run_node=run_node)
        return {
            "decision": {"agent": "SupervisorTaskGraph", "success": bool(result.get("ok")), "graph_result": result},
            "budget": self.cost_guard.status(),
            "blacklisted_agents": list(self.blacklist.blacklisted),
            "mission_id": mission_id,
            "working_memory": self.working_memory.list(mission_id, limit=50),
        }

    def _update_agent_state(self, agent_name: str, status: str):
        """
        Persist agent lifecycle status using ExecutionEngine (no bypass).
        Uses existing `agents` table created by db_init.
        """

        exec_plan = {
            "goal": f"update agent state {agent_name} -> {status}",
            "steps": ["execute"],
            "autonomy_level": "LIMITED_AUTONOMY",
            "_permission_context": "supervisor_agent",
            "assumed_failure": "db_update_fails",
            "failure_impact": "agent_state_not_updated",
            "confidence_score": 80,
        }

        def action(_p):
            def _write(conn):
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM agents WHERE name=?", (agent_name,))
                row = cursor.fetchone()
                if not row:
                    cursor.execute(
                        "INSERT INTO agents (name, status) VALUES (?, ?)",
                        (agent_name, status),
                    )
                else:
                    cursor.execute(
                        "UPDATE agents SET status=? WHERE name=?",
                        (status, agent_name),
                    )

                cursor.execute(
                    "INSERT INTO agent_actions (agent_name, action, result) VALUES (?, ?, ?)",
                    (agent_name, "state_update", status),
                )
                conn.commit()
                return None

            run_db_write_with_retry("agents.upsert_status", _write)
            return {"agent": agent_name, "status": status}

        def rollback(_p):
            # Conservative rollback: set agent back to ACTIVE (most permissive safe state).
            def _write(conn):
                cursor = conn.cursor()
                cursor.execute("UPDATE agents SET status='ACTIVE' WHERE name=?", (agent_name,))
                conn.commit()
                return None

            run_db_write_with_retry("agents.rollback_to_active", _write)

        self.exec_engine.execute(exec_plan, action, rollback=rollback)

    def _hibernate_if_inactive(self, *, hours: int = 6):
        """
        Hibernation policy (docs/NOVA_AGENT_LIFECYCLE.md):
        - If a persisted agent has no recent activity, mark it HIBERNATED.
        We infer activity from `agent_actions` timestamps (no schema changes).
        """
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)

        exec_plan = {
            "goal": "hibernate inactive agents",
            "steps": ["execute"],
            "autonomy_level": "LIMITED_AUTONOMY",
            "_permission_context": "supervisor_agent",
            "assumed_failure": "hibernation_query_or_update_fails",
            "failure_impact": "agents_remain_active",
            "confidence_score": 80,
        }

        def action(_p):
            def _write(conn):
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT a.name
                    FROM agents a
                    LEFT JOIN agent_actions aa
                      ON aa.agent_name = a.name
                    GROUP BY a.name
                    HAVING MAX(COALESCE(aa.created_at, '1970-01-01')) < ?
                       AND a.status IN ('ACTIVE','IDLE')
                    """,
                    (cutoff,),
                )
                rows = cursor.fetchall()
                names = [r["name"] for r in rows] if rows else []
                for n in names:
                    cursor.execute("UPDATE agents SET status='HIBERNATED' WHERE name=?", (n,))
                conn.commit()
                return names

            names = run_db_write_with_retry("agents.hibernate_inactive", _write)
            return {"hibernated": names}

        def rollback(_p):
            return None

        self.exec_engine.execute(exec_plan, action, rollback=rollback)
