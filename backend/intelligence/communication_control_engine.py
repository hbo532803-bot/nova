from __future__ import annotations

import json
from typing import Any, Dict

from backend.database import get_db
from backend.intelligence.lead_interaction_engine import LeadInteractionEngine
from backend.system.audit_log import audit_log


class CommunicationControlEngine:
    """
    Generates communication suggestions and stores conversation context.
    All outbound messages remain approval-gated.
    """

    def __init__(self) -> None:
        self.leads = LeadInteractionEngine()

    def suggest_reply(
        self,
        *,
        lead_id: int,
        experiment_id: int,
        channel: str,
        user_message: str,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        lead = self._get_lead(int(lead_id))
        if not lead:
            return {"error": "lead_not_found"}

        intent = str(lead["intent_level"] or "low")
        tone = "concise and consultative" if intent in {"high", "medium"} else "educational and low-pressure"
        context_map = context or {}
        response = (
            f"Thanks for sharing this. Based on your goals, I recommend a short discovery call to align on scope and timeline. "
            f"I can share a tailored {str(context_map.get('service_type','service'))} plan with clear deliverables and pricing tiers."
        )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_context
                (lead_id, experiment_id, channel, user_message, assistant_suggestion, context_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(lead_id), int(experiment_id), str(channel), str(user_message), response, json.dumps(context_map)),
            )
            context_id = int(cursor.lastrowid)
            conn.commit()

        queued = self.leads.queue_message_for_approval(
            lead_id=int(lead_id),
            experiment_id=int(experiment_id),
            channel=str(channel),
            message_body=response,
        )
        audit_log(actor="communication_control", action="communication.suggested", target=str(context_id), payload={"queue": queued, "tone": tone})
        return {
            "context_id": context_id,
            "lead_id": int(lead_id),
            "channel": str(channel),
            "intent_level": intent,
            "tone": tone,
            "suggested_reply": response,
            "approval_queue": queued,
        }

    def _get_lead(self, lead_id: int) -> Any:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, intent_level FROM leads WHERE id=?", (int(lead_id),))
            return cursor.fetchone()
