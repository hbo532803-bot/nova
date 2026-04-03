import threading
from datetime import datetime

from backend.agents.supervisor import SupervisorAgent
from backend.frontend_api.event_bus import broadcast
from backend.database import get_db
from backend.intelligence.decision_matrix import DecisionMatrix
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.execution.action_types import ActionType
import re
from backend.intelligence.playbooks.library import get_playbook
from backend.intelligence.mission_planner import MissionPlanner


class NovaCore:
    """
    Central decision brain of Nova.
    All commands (user or autonomous) must pass here.
    """

    def __init__(self):

        self.supervisor = SupervisorAgent()
        self.decision_matrix = DecisionMatrix()
        self.confidence = ConfidenceEngine()

        # Prevent concurrent execution collisions
        self._lock = threading.Lock()

        # Nova runtime state
        self.last_command = None
        self.last_result = None

    # ====================================
    # PUBLIC ENTRYPOINT
    # ====================================

    def handle_command(self, command: str):

        with self._lock:

            self.last_command = command

            broadcast({
                "type": "log",
                "level": "info",
                "message": f"NovaCore received command: {command}"
            })

            plan = self._create_plan(command)

            result = self._execute(plan)

            self.last_result = result

            self._log_decision(plan, result)

            return result

    def requirement_to_command(self, requirement: dict) -> str:
        """
        Integration hook: convert structured user requirement into a command string
        that keeps execution routed through NovaCore.
        """
        service = str(requirement.get("service") or "consultation")
        goal = str(requirement.get("goal") or "").strip()
        details = requirement.get("details") or {}
        offers = details.get("offers") or []
        preferred = next((o for o in offers if o.get("tier") == "STANDARD"), offers[0] if offers else None)
        tier = str((preferred or {}).get("tier") or "STANDARD")
        return f"run mission {service}: {goal} [{tier}]"

    # ====================================
    # PLAN CREATION
    # ====================================

    def _create_plan(self, command: str):

        confidence_state = self.confidence.get_state()
        confidence_score = int(confidence_state["score"])

        plan = {
            "goal": command,
            "steps": [],
            "actions": [],
            "required_capabilities": [],
            "autonomy_level": "LIMITED_AUTONOMY",
            "_permission_context": "nova_core",
            "created_at": datetime.utcnow().isoformat(),
            "confidence_score": confidence_score,
            # ExecutionEngine precheck requires failure-first simulation fields.
            "assumed_failure": "execution_fails_or_returns_unexpected_output",
            "failure_impact": "no_state_change_or_partial_state_change; rollback_required",
        }

        cmd = command.lower()

        m = re.match(r"^\s*run\s+mission\s+(.+)\s*$", cmd)
        if m:
            goal = m.group(1).strip()
            mission_id = plan["created_at"]
            task_graph = MissionPlanner().build_task_graph(goal, mission_id=mission_id)
            plan["steps"] = ["execute"]
            plan["task_graph"] = task_graph
            plan["actions"] = [{"type": ActionType.REFLECTION_RECORD.value, "payload": {"reflection": {
                "cycle_id": mission_id,
                "primary_goal_snapshot": command,
                "input_objective": goal,
                "execution_result": "mission_planned",
                "success": True,
                "confidence_before": confidence_score,
                "confidence_after": confidence_score,
            }}}]
            plan["required_capabilities"] = ["analysis", "research", "growth_experimentation"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        # Internal system command: state transitions (NovaBrainLoop controls these)
        if cmd.startswith("__state__:"):
            target_state = command.split(":", 1)[1].strip()
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.STATE_TRANSITION.value,
                "payload": {"state": target_state},
                "assumed_failure": "state_persist_fails",
                "failure_impact": "state_machine_inconsistent",
            }]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        # Command grammar for console-driven action requests (no bypass):
        # - "run experiment <id>"
        m = re.match(r"^\s*attach\s+playbook\s+([a-z0-9_\-]+)\s+to\s+experiment\s+(\d+)\s*$", cmd)
        if m:
            playbook_name = m.group(1)
            exp_id = int(m.group(2))
            playbook = get_playbook(playbook_name)
            if not playbook:
                plan["steps"] = ["execute"]
                plan["actions"] = [{
                    "type": ActionType.REFLECTION_RECORD.value,
                    "payload": {"reflection": {
                        "cycle_id": plan["created_at"],
                        "primary_goal_snapshot": command,
                        "input_objective": command,
                        "execution_result": f"unknown_playbook:{playbook_name}",
                        "success": False,
                        "confidence_before": confidence_score,
                        "confidence_after": confidence_score,
                    }},
                    "assumed_failure": "reflection_write_fails",
                    "failure_impact": "learning_signal_lost",
                }]
                decision = self.decision_matrix.evaluate(plan)
                plan["decision_matrix"] = decision
                return plan

            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.PLAYBOOK_ATTACH.value,
                "payload": {"experiment_id": exp_id, "playbook_name": playbook_name, "playbook": playbook},
                "assumed_failure": "playbook_attach_fails",
                "failure_impact": "experiment_missing_playbook",
            }]
            plan["required_capabilities"] = ["growth_experimentation", "finance"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        m = re.match(r"^\s*run\s+experiment\s+(\d+)\s*$", cmd)
        if m:
            exp_id = int(m.group(1))
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.EXPERIMENT_RUN.value,
                "payload": {"experiment_id": exp_id},
                "assumed_failure": "experiment_run_fails",
                "failure_impact": "experiment_not_executed",
            }]
            plan["required_capabilities"] = ["traffic", "engagement"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("learn strategy", "strategy learn", "run strategy learning"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.STRATEGY_LEARN.value,
                "payload": {"lookback": 100},
                "assumed_failure": "strategy_learning_fails",
                "failure_impact": "no_strategy_adjustment_applied",
            }]
            plan["required_capabilities"] = ["analysis", "finance"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("health check", "system health check"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.HEALTH_CHECK.value,
                "payload": {},
                "assumed_failure": "health_check_fails",
                "failure_impact": "no_stability_signal",
            }]
            plan["required_capabilities"] = ["analysis"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("recover system", "system recover", "stability recover"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.RECOVER_SYSTEM.value,
                "payload": {},
                "assumed_failure": "recovery_fails",
                "failure_impact": "system_remains_unstable",
            }]
            plan["required_capabilities"] = ["agent_ops", "analysis"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("evaluate portfolio", "portfolio evaluate", "experiments evaluate"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.EXPERIMENT_EVALUATE_PORTFOLIO.value,
                "payload": {"limit": 50},
                "assumed_failure": "portfolio_evaluate_fails",
                "failure_impact": "no_lifecycle_automation_signal",
            }]
            plan["required_capabilities"] = ["analysis", "finance"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("research opportunities", "run research", "research run"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.RESEARCH_RUN.value,
                "payload": {"max_proposals": 5},
                "assumed_failure": "research_engine_fails",
                "failure_impact": "no_new_opportunities",
            }]
            plan["required_capabilities"] = ["research", "opportunity_discovery"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        m = re.match(r"^\s*create\s+agent\s+for\s+(.+)\s*$", cmd)
        if m:
            caps = [c.strip() for c in m.group(1).split(",") if c.strip()]
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.AGENT_FACTORY_CREATE.value,
                "payload": {"required_capabilities": caps},
                "assumed_failure": "agent_factory_create_fails",
                "failure_impact": "capability_gap_persists",
            }]
            plan["required_capabilities"] = ["agent_ops", "analysis"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("evolve agents", "agent factory evolve", "evolve agent factory"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.AGENT_FACTORY_EVOLVE.value,
                "payload": {},
                "assumed_failure": "agent_factory_evolve_fails",
                "failure_impact": "ineffective_agents_not_retired",
            }]
            plan["required_capabilities"] = ["agent_ops", "analysis"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        m = re.match(r"^\s*hibernate\s+agent\s+(\d+)\s*$", cmd)
        if m:
            agent_id = int(m.group(1))
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.AGENT_HIBERNATE.value,
                "payload": {"agent_id": agent_id},
                "assumed_failure": "agent_hibernate_fails",
                "failure_impact": "agent_remains_active",
            }]
            plan["required_capabilities"] = ["agent_ops"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        m = re.match(r"^\s*wake\s+agent\s+(\d+)\s*$", cmd)
        if m:
            agent_id = int(m.group(1))
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.AGENT_WAKE.value,
                "payload": {"agent_id": agent_id},
                "assumed_failure": "agent_wake_fails",
                "failure_impact": "agent_remains_hibernated",
            }]
            plan["required_capabilities"] = ["agent_ops"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        m = re.match(r"^\s*opportunity\s+(approve|reject|convert)\s+(\d+)\s*$", cmd)
        if m:
            verb = m.group(1)
            proposal_id = int(m.group(2))
            action_map = {
                "approve": ActionType.OPPORTUNITY_APPROVE.value,
                "reject": ActionType.OPPORTUNITY_REJECT.value,
                "convert": ActionType.OPPORTUNITY_CONVERT.value,
            }
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": action_map[verb],
                "payload": {"proposal_id": proposal_id},
                "assumed_failure": f"opportunity_{verb}_fails",
                "failure_impact": "proposal_state_not_updated_or_experiment_not_created",
            }]
            plan["required_capabilities"] = ["opportunity_discovery", "finance"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if cmd.strip() in ("discover opportunities", "discover opportunity", "opportunity discover"):
            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.OPPORTUNITY_DISCOVER.value,
                "payload": {},
                "assumed_failure": "opportunity_discovery_fails",
                "failure_impact": "no_new_proposals",
            }]
            plan["required_capabilities"] = ["opportunity_discovery", "research"]
            decision = self.decision_matrix.evaluate(plan)
            plan["decision_matrix"] = decision
            return plan

        if "analyze" in cmd:

            plan["steps"] = ["analyze"]

        elif "optimize" in cmd:

            plan["steps"] = ["analyze", "execute"]

        elif "market" in cmd:

            plan["steps"] = ["market_scan"]
            plan["actions"] = [{
                "type": ActionType.MARKET_SCAN.value,
                "payload": {},
                "assumed_failure": "market_pipeline_fails",
                "failure_impact": "missed_opportunities_for_interval",
            }]

        elif "experiment" in cmd:

            plan["steps"] = ["experiment"]
            plan["actions"] = [{
                "type": ActionType.EXPERIMENT_CREATE.value,
                "payload": {},
                "assumed_failure": "experiment_creation_fails",
                "failure_impact": "no_experiments_launched",
            }]

        else:

            plan["steps"] = ["execute"]
            plan["actions"] = [{
                "type": ActionType.REFLECTION_RECORD.value,
                "payload": {"reflection": {
                    "cycle_id": plan["created_at"],
                    "primary_goal_snapshot": command,
                    "input_objective": command,
                    "execution_result": "noop",
                    "success": True,
                    "confidence_before": confidence_score,
                    "confidence_after": confidence_score,
                }},
                "assumed_failure": "reflection_write_fails",
                "failure_impact": "learning_signal_lost",
            }]

        decision = self.decision_matrix.evaluate(plan)
        plan["decision_matrix"] = decision

        outcome = decision["outcome"]
        if outcome == "PLANNING_ONLY":
            plan["autonomy_level"] = "MANUAL_ONLY"
        elif outcome == "REQUIRES_HUMAN_APPROVAL":
            plan["autonomy_level"] = "HUMAN_APPROVAL_REQUIRED"
        elif outcome == "REJECTED":
            plan["autonomy_level"] = "MANUAL_ONLY"
            plan["rejected"] = True

        return plan

    # ====================================
    # EXECUTION
    # ====================================

    def _execute(self, plan):

        try:
            if plan.get("rejected"):
                return {
                    "success": False,
                    "error": "DecisionMatrix rejected plan",
                    "decision_matrix": plan.get("decision_matrix"),
                }

            broadcast({
                "type": "log",
                "level": "think",
                "message": "Supervisor executing plan"
            })

            result = self.supervisor.handle(plan)

            broadcast({
                "type": "log",
                "level": "info",
                "message": "Plan executed successfully"
            })

            return result

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "error",
                "message": f"Execution failed: {e}"
            })

            return {
                "success": False,
                "error": str(e)
            }

    # ====================================
    # DECISION MEMORY
    # ====================================

    def _log_decision(self, plan, result):

        try:

            with get_db() as conn:
             cursor = conn.cursor()

             cursor.execute(
                """
                INSERT INTO decision_memory
                (decision_type, context_snapshot, actual_outcome, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "nova_core",
                    str(plan),
                    str(result),
                    datetime.utcnow().isoformat()
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "warn",
                "message": f"Decision logging failed: {e}"
            })


_nova_core_instance: NovaCore | None = None
_nova_core_init_lock = threading.Lock()


def get_nova_core() -> NovaCore:
    """
    Lazy singleton getter.
    Prevents heavy subsystem initialization at import time.
    """
    global _nova_core_instance
    if _nova_core_instance is None:
        with _nova_core_init_lock:
            if _nova_core_instance is None:
                _nova_core_instance = NovaCore()
    return _nova_core_instance
