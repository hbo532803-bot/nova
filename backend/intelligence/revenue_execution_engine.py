from __future__ import annotations

import json
from typing import Any, Dict, List

from backend.database import get_db
from backend.intelligence.traffic_engine import TrafficEngine
from backend.system.audit_log import audit_log


class RevenueExecutionEngine:
    """
    Converts priority decisions into executable actions with safety controls.
    Real-world readiness: queues external communication actions for approval.
    """

    def __init__(self) -> None:
        self.traffic = TrafficEngine()

    def execute_for_experiment(self, experiment_id: int, *, priority_level: str, decision: str) -> Dict[str, Any]:
        actions = self._build_actions(priority_level=str(priority_level), decision=str(decision))
        queued: List[Dict[str, Any]] = []
        for action in actions:
            queued.append(self._queue_action(experiment_id=experiment_id, action=action))
        audit_log(actor="revenue_execution", action="execution.plan", target=str(experiment_id), payload={"priority": priority_level, "decision": decision, "count": len(queued)})
        return {"experiment_id": int(experiment_id), "queued_actions": queued}

    def run_pending_actions(self, *, experiment_id: int | None = None) -> Dict[str, Any]:
        where = "WHERE status='PENDING'"
        params: list[Any] = []
        if experiment_id is not None:
            where += " AND experiment_id=?"
            params.append(int(experiment_id))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, experiment_id, action_type, channel, payload_json, requires_approval
                FROM execution_actions
                {where}
                ORDER BY id ASC
                LIMIT 50
                """,
                tuple(params),
            )
            rows = cursor.fetchall()

        outcomes = []
        for row in rows:
            payload = json.loads(str(row["payload_json"] or "{}"))
            needs_approval = bool(row["requires_approval"])
            if needs_approval:
                outcomes.append(self._mark_waiting(row["id"]))
                continue
            outcomes.append(self._execute_action(row["id"], int(row["experiment_id"] or 0), str(row["action_type"]), str(row["channel"] or "manual"), payload))
        return {"processed": len(outcomes), "outcomes": outcomes}

    def _execute_action(self, action_id: int, experiment_id: int, action_type: str, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if action_type in {"increase_traffic", "reduce_traffic", "stop_execution"}:
            self.traffic.record_visit(mission_id=str(experiment_id), source=f"execution:{channel}", referral=action_type)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE execution_actions SET status='EXECUTED' WHERE id=?", (int(action_id),))
            conn.commit()

        audit_log(actor="revenue_execution", action=f"execution.{action_type}", target=str(experiment_id), payload=payload)
        return {"action_id": action_id, "status": "EXECUTED", "action_type": action_type}

    def _mark_waiting(self, action_id: int) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE execution_actions SET status='WAITING_APPROVAL' WHERE id=?", (int(action_id),))
            conn.commit()
        return {"action_id": int(action_id), "status": "WAITING_APPROVAL"}

    def _queue_action(self, *, experiment_id: int, action: Dict[str, Any]) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO execution_actions (experiment_id, action_type, channel, payload_json, status, requires_approval)
                VALUES (?, ?, ?, ?, 'PENDING', ?)
                """,
                (
                    int(experiment_id),
                    str(action["action_type"]),
                    str(action.get("channel") or "manual"),
                    json.dumps(action.get("payload") or {}),
                    1 if bool(action.get("requires_approval")) else 0,
                ),
            )
            action_id = int(cursor.lastrowid)
            conn.commit()
        return {"action_id": action_id, **action}

    def _build_actions(self, *, priority_level: str, decision: str) -> List[Dict[str, Any]]:
        if priority_level == "HIGH" and decision in {"scale", "hold", "optimize"}:
            return [
                {"action_type": "increase_traffic", "channel": "content_posts", "payload": {"mode": "manual"}, "requires_approval": False},
                {"action_type": "duplicate_funnel", "channel": "inbound_tracking", "payload": {"variation": "A/B"}, "requires_approval": False},
                {"action_type": "test_variations", "channel": "content_posts", "payload": {"count": 2}, "requires_approval": False},
                {"action_type": "outreach", "channel": "outreach", "payload": {"template": "human_review_required"}, "requires_approval": True},
            ]
        if priority_level == "LOW" or decision in {"fail"}:
            return [
                {"action_type": "reduce_traffic", "channel": "manual", "payload": {"delta": -0.5}, "requires_approval": False},
                {"action_type": "stop_execution", "channel": "manual", "payload": {"reason": "low_priority_or_fail"}, "requires_approval": False},
            ]
        return [{"action_type": "monitor", "channel": "inbound_tracking", "payload": {}, "requires_approval": False}]
