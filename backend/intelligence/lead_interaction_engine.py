from __future__ import annotations

import json
from typing import Any, Dict

from backend.database import get_db
from backend.system.audit_log import audit_log


class LeadInteractionEngine:
    """
    Lead capture + intent classification with explicit human approval
    before any external communication.
    """

    def capture_lead(
        self,
        *,
        mission_id: str,
        name: str,
        email: str = "",
        phone: str = "",
        source: str = "inbound",
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        meta = metadata or {}
        intent = self._classify_intent(meta)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO leads (mission_id, name, email, phone, source, intent_level, intent_score, approved_for_contact, last_interaction_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (mission_id, name, email, phone, source, intent["level"], intent["score"], source),
            )
            lead_id = int(cursor.lastrowid)
            conn.commit()
        audit_log(actor="lead_engine", action="lead.capture", target=str(lead_id), payload={"intent": intent, "source": source})
        return {"lead_id": lead_id, "intent": intent, "requires_approval_for_contact": True}

    def queue_message_for_approval(self, *, lead_id: int, experiment_id: int, channel: str, message_body: str) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM communication_queue
                WHERE lead_id=? AND experiment_id=? AND channel=? AND status IN ('PENDING_APPROVAL','APPROVED')
                ORDER BY id DESC LIMIT 1
                """,
                (int(lead_id), int(experiment_id), str(channel)),
            )
            existing = cursor.fetchone()
            if existing:
                return {"queue_id": int(existing["id"]), "status": "ALREADY_QUEUED"}
            cursor.execute(
                """
                INSERT INTO communication_queue (lead_id, experiment_id, channel, message_body, status)
                VALUES (?, ?, ?, ?, 'PENDING_APPROVAL')
                """,
                (int(lead_id), int(experiment_id), str(channel), str(message_body)),
            )
            queue_id = int(cursor.lastrowid)
            conn.commit()
        audit_log(actor="lead_engine", action="communication.queued", target=str(queue_id), payload={"lead_id": lead_id, "channel": channel})
        return {"queue_id": queue_id, "status": "PENDING_APPROVAL"}

    def approve_queued_message(self, *, queue_id: int, approved_by: str) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE communication_queue
                SET status='APPROVED', approved_by=?, approved_at=datetime('now')
                WHERE id=? AND status='PENDING_APPROVAL'
                """,
                (str(approved_by), int(queue_id)),
            )
            ok = cursor.rowcount > 0
            if ok:
                cursor.execute(
                    """
                    UPDATE leads
                    SET approved_for_contact=1
                    WHERE id=(SELECT lead_id FROM communication_queue WHERE id=?)
                    """,
                    (int(queue_id),),
                )
            conn.commit()
        audit_log(actor=str(approved_by), action="communication.approve", target=str(queue_id), payload={"approved": ok})
        return {"queue_id": int(queue_id), "approved": bool(ok)}

    def _classify_intent(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        score = 0.0
        if metadata.get("requested_demo"):
            score += 0.5
        if metadata.get("budget_confirmed"):
            score += 0.3
        if metadata.get("timeline_days") and float(metadata.get("timeline_days")) <= 14:
            score += 0.2
        level = "high" if score >= 0.7 else ("medium" if score >= 0.3 else "low")
        return {"level": level, "score": round(score, 2), "metadata": json.dumps(metadata)}
