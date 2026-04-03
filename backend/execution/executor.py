"""
Executor entrypoint used by hardened_executor.

Architecture constraints (docs):
- Execution must pass through ExecutionEngine.
- Agents cannot execute system actions directly.
- Subsystem calls must be invoked via the engine's action callable.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.execution.execution_engine import ExecutionEngine
from backend.execution.action_router import ActionRouter
from backend.execution.action_types import ActionType
from backend.frontend_api.event_bus import broadcast
from backend.tools.rollback_manager import rollback_last
from backend.system.audit_log import audit_log
from backend.services.result_collector import ResultCollector
from backend.services.delivery_service import DeliveryService


def execute_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stable public API.
    Runs plan steps through ExecutionEngine with rollback guarantees.
    """
    engine = ExecutionEngine()
    router = ActionRouter()
    collector = ResultCollector()
    delivery = DeliveryService()
    mission_id = str(plan.get("mission_id") or plan.get("created_at") or "")
    order_id = str(plan.get("order_id") or "")

    actions = plan.get("actions") or []
    if not actions:
        aggregated = collector.collect_outputs(mission_id=mission_id or None, order_id=order_id or None)
        return {
            "success": True,
            "data": {"info": "no actions", "goal": plan.get("goal")},
            "error": None,
            "rolled_back": False,
            "duration_ms": 0,
            "result": delivery.build_final_result(aggregated, type_hint=str(plan.get("goal") or "")),
        }

    results: list[dict] = []
    overall_success = True
    rollback_stack: list[dict] = []

    for idx, act in enumerate(actions):
        act_type = str(act.get("type"))

        action_plan = {
            "goal": f"{plan.get('goal')} :: {act_type} [{idx}]",
            "steps": ["execute"],
            "autonomy_level": plan.get("autonomy_level", "LIMITED_AUTONOMY"),
            "_permission_context": plan.get("_permission_context", "executor"),
            "confidence_score": plan.get("confidence_score", 50),
            "assumed_failure": act.get("assumed_failure") or plan.get("assumed_failure") or "action_fails",
            "failure_impact": act.get("failure_impact") or plan.get("failure_impact") or "unknown_impact",
        }

        def do_action(p: Dict[str, Any], _act=act) -> Any:
            res = router.run(_act, p)
            # Best-effort audit trail for each action execution.
            audit_log(
                actor=str(plan.get("_actor") or ""),
                action="ACTION_EXECUTE",
                target=str(_act.get("type")),
                payload={"payload": _act.get("payload"), "plan_goal": plan.get("goal")},
            )

            # Capture rollback hints for file-backed changes (diff_engine applies backups).
            try:
                if isinstance(res, dict) and res.get("backup"):
                    payload = _act.get("payload") or {}
                    path = payload.get("path")
                    if path:
                        rollback_stack.append({"type": "ROLLBACK_FILE", "path": str(path)})
            except Exception:
                pass
            return res

        def rollback(_p: Dict[str, Any]) -> None:
            # Real rollback for file-backed changes we observed in this plan.
            for item in reversed(rollback_stack):
                if item.get("type") == "ROLLBACK_FILE":
                    rollback_last(str(item.get("path")))
            return None

        exec_result = engine.execute(action_plan, do_action, rollback=rollback)
        results.append(
            {
                "type": act_type,
                "success": bool(exec_result.success),
                "data": exec_result.data,
                "error": exec_result.error,
                "rolled_back": exec_result.rolled_back,
                "duration_ms": exec_result.duration_ms,
            }
        )
        collector.store_task_output(
            mission_id,
            key=f"action:{idx}:{act_type}",
            output=results[-1],
        )

        # Always record reflection as an action routed through the spine.
        try:
            reflection_action = {
                "type": ActionType.REFLECTION_RECORD.value,
                "payload": {
                    "reflection": {
                        "cycle_id": str(plan.get("created_at") or ""),
                        "primary_goal_snapshot": str(plan.get("goal") or ""),
                        "input_objective": str(plan.get("goal") or ""),
                        "execution_result": str(exec_result.data if exec_result.success else exec_result.error),
                        "success": bool(exec_result.success),
                        "confidence_before": float(plan.get("confidence_score") or 0),
                        "confidence_after": float(plan.get("confidence_score") or 0),
                    }
                },
            }
            reflection_plan = {
                **action_plan,
                "goal": f"{plan.get('goal')} :: REFLECTION_RECORD",
                "assumed_failure": "reflection_write_fails",
                "failure_impact": "learning_signal_lost",
            }
            engine.execute(reflection_plan, lambda p, a=reflection_action: router.run(a, p), rollback=rollback)
        except Exception:
            pass

        if not exec_result.success:
            overall_success = False
            # Roll back any observed file changes for this plan immediately on failure.
            try:
                rollback(action_plan)
            except Exception:
                pass

    execution_payload = {
        "success": overall_success,
        "data": {"actions": results},
        "error": None if overall_success else "one_or_more_actions_failed",
        "rolled_back": any(r["rolled_back"] for r in results),
        "duration_ms": sum(int(r["duration_ms"] or 0) for r in results),
    }

    try:
        aggregated = collector.collect_outputs(mission_id=mission_id or None, order_id=order_id or None)
        execution_payload["result"] = delivery.build_final_result(
            aggregated,
            type_hint=str(plan.get("goal") or ""),
        )
    except Exception:
        # Do not alter execution success path if result assembly fails.
        pass

    return execution_payload
