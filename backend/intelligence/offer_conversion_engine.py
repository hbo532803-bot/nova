from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.database import get_db
from backend.intelligence.lead_interaction_engine import LeadInteractionEngine
from backend.system.audit_log import audit_log


class OfferConversionEngine:
    def __init__(self) -> None:
        self.leads = LeadInteractionEngine()

    def create_offer_for_lead(self, *, lead_id: int, experiment_id: Optional[int] = None, service_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lead = self._get_lead(int(lead_id))
        if not lead:
            return {"error": "lead_not_found"}

        selected_service = service_type or self._select_service_type(lead, context or {})
        tier = self._select_tier(lead, context or {})
        offer_row = self._get_offer_catalog(selected_service, tier)
        if not offer_row:
            return {"error": "offer_not_found", "service_type": selected_service, "tier": tier}

        pricing = self.calculate_dynamic_price(service_type=selected_service, tier=tier)
        payload = {
            "service_type": selected_service,
            "tier": tier,
            "deliverables": json.loads(str(offer_row["deliverables_json"] or "[]")),
            "expected_outcome": str(offer_row["expected_outcome"] or ""),
            "value_summary": self._build_value_summary(selected_service, tier, str(offer_row["expected_outcome"] or "")),
            "pricing": pricing,
            "intent_level": str(lead["intent_level"] or "low"),
        }

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversion_attempts
                (lead_id, experiment_id, service_type, tier, offer_payload_json, proposed_price, status)
                VALUES (?, ?, ?, ?, ?, ?, 'DRAFT')
                """,
                (int(lead_id), int(experiment_id) if experiment_id is not None else None, selected_service, tier, json.dumps(payload), float(pricing["final_price"])),
            )
            attempt_id = int(cursor.lastrowid)
            conn.commit()

        audit_log(actor="offer_conversion", action="offer.created", target=str(attempt_id), payload={"lead_id": lead_id, "service_type": selected_service, "tier": tier, "price": pricing["final_price"]})
        return {"attempt_id": attempt_id, "lead_id": int(lead_id), "experiment_id": int(experiment_id) if experiment_id is not None else None, "offer": payload, "status": "DRAFT"}

    def queue_offer_response_for_approval(self, *, attempt_id: int, channel: str = "email") -> Dict[str, Any]:
        attempt = self._get_attempt(int(attempt_id))
        if not attempt:
            return {"error": "attempt_not_found"}
        offer = json.loads(str(attempt["offer_payload_json"] or "{}"))
        queued = self.leads.queue_message_for_approval(lead_id=int(attempt["lead_id"]), experiment_id=int(attempt["experiment_id"] or 0), channel=str(channel), message_body=self._build_offer_message(offer))
        with get_db() as conn:
            cursor = conn.cursor()
            new_status = "PENDING_APPROVAL" if queued.get("status") in {"PENDING_APPROVAL", "ALREADY_QUEUED"} else "DRAFT"
            offer["communication_queue"] = {"queue_id": queued.get("queue_id"), "channel": channel, "status": queued.get("status")}
            cursor.execute("UPDATE conversion_attempts SET status=?, offer_payload_json=? WHERE id=?", (new_status, json.dumps(offer), int(attempt_id)))
            conn.commit()
        return {"attempt_id": int(attempt_id), "queue": queued, "status": new_status}

    def mark_real_payment(self, *, attempt_id: int, amount: float, approved_by: str = "system") -> Dict[str, Any]:
        attempt = self._get_attempt(int(attempt_id))
        if not attempt:
            return {"error": "attempt_not_found"}
        if float(amount) <= 0:
            return {"error": "invalid_amount"}
        experiment_id = int(attempt["experiment_id"] or 0)
        mission_id = str(experiment_id or attempt["lead_id"])
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO revenue_events (mission_id, lead_id, amount, status, source) VALUES (?, ?, ?, 'CONFIRMED', 'real_payment')", (mission_id, int(attempt["lead_id"]), float(amount)))
            if experiment_id:
                cursor.execute("UPDATE economic_experiments SET revenue_generated=COALESCE(revenue_generated,0)+?, revenue_real_payment=COALESCE(revenue_real_payment,0)+?, revenue_source='real_payment' WHERE id=?", (float(amount), float(amount), experiment_id))
            cursor.execute("UPDATE conversion_attempts SET status='CONVERTED', approved_by=?, approved_at=datetime('now'), converted_at=datetime('now') WHERE id=?", (str(approved_by), int(attempt_id)))
            conn.commit()
        audit_log(actor=str(approved_by), action="conversion.real_payment", target=str(attempt_id), payload={"amount": float(amount), "experiment_id": experiment_id})
        return {"attempt_id": int(attempt_id), "lead_id": int(attempt["lead_id"]), "experiment_id": experiment_id or None, "amount": float(amount), "revenue_source": "real_payment", "status": "CONVERTED"}

    def calculate_dynamic_price(self, *, service_type: str, tier: str) -> Dict[str, float]:
        offer_row = self._get_offer_catalog(service_type, tier)
        if not offer_row:
            return {"base_price": 0.0, "demand_factor": 1.0, "conversion_factor": 1.0, "success_factor": 1.0, "final_price": 0.0}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS n FROM conversion_attempts WHERE service_type=? AND tier=? AND created_at >= datetime('now','-30 days')", (str(service_type), str(tier)))
            demand_n = int((cursor.fetchone()["n"] or 0))
            cursor.execute("SELECT COALESCE(SUM(CASE WHEN status='CONVERTED' THEN 1 ELSE 0 END),0) AS converted, COUNT(*) AS total, COALESCE(AVG(CASE WHEN status='CONVERTED' THEN proposed_price END),0) AS avg_win_price FROM conversion_attempts WHERE service_type=? AND tier=?", (str(service_type), str(tier)))
            row = cursor.fetchone()
        converted = float((row["converted"] or 0.0) if row else 0.0)
        total = float((row["total"] or 0.0) if row else 0.0)
        conversion_rate = (converted / total) if total else 0.0
        avg_win_price = float((row["avg_win_price"] or 0.0) if row else 0.0)
        base_price = float(offer_row["base_price"] or 0.0)
        demand_factor = max(0.9, min(1.25, 1.0 + (demand_n * 0.01)))
        conversion_factor = max(0.85, min(1.2, 0.9 + conversion_rate))
        success_anchor = avg_win_price if avg_win_price > 0 else base_price
        success_factor = max(0.9, min(1.15, success_anchor / base_price if base_price else 1.0))
        return {"base_price": round(base_price, 2), "demand_factor": round(demand_factor, 4), "conversion_factor": round(conversion_factor, 4), "success_factor": round(success_factor, 4), "final_price": float(round(base_price * demand_factor * conversion_factor * success_factor, 2))}

    def conversion_feedback(self, *, limit: int = 20) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service_type, tier, COUNT(*) AS attempts, COALESCE(SUM(CASE WHEN status='CONVERTED' THEN 1 ELSE 0 END),0) AS converted, COALESCE(AVG(proposed_price),0) AS avg_price, COALESCE(SUM(CASE WHEN status='CONVERTED' THEN proposed_price ELSE 0 END),0) AS earned FROM conversion_attempts GROUP BY service_type, tier ORDER BY earned DESC, converted DESC LIMIT ?", (int(limit),))
            rows = cursor.fetchall()
        ranking: List[Dict[str, Any]] = []
        for row in rows:
            attempts = int(row["attempts"] or 0)
            converted = int(row["converted"] or 0)
            ranking.append({"service_type": str(row["service_type"]), "tier": str(row["tier"]), "attempts": attempts, "converted": converted, "conversion_rate": round((converted / attempts) if attempts else 0.0, 4), "avg_price": round(float(row["avg_price"] or 0.0), 2), "earned": round(float(row["earned"] or 0.0), 2)})
        return {"best_offer": (ranking[0] if ranking else None), "ranking": ranking}

    def _select_service_type(self, lead: Any, context: Dict[str, Any]) -> str:
        requested = str(context.get("service_type") or "").strip().lower()
        if requested in {"website_development", "lead_generation", "automation"}:
            return requested
        source = str((lead["source"] or "")).lower()
        if "web" in source:
            return "website_development"
        if "automation" in source:
            return "automation"
        return "lead_generation"

    def _select_tier(self, lead: Any, context: Dict[str, Any]) -> str:
        intent = str(lead["intent_level"] or "low").lower()
        is_business = bool(context.get("is_business") or context.get("company_name") or context.get("business_type"))
        if intent == "high" and is_business:
            return "premium"
        if intent in {"high", "medium"}:
            return "standard"
        return "basic"

    def _get_offer_catalog(self, service_type: str, tier: str) -> Any:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, service_type, tier, deliverables_json, expected_outcome, base_price FROM offer_catalog WHERE service_type=? AND tier=? AND is_active=1 LIMIT 1", (str(service_type), str(tier)))
            return cursor.fetchone()

    def _get_lead(self, lead_id: int) -> Any:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, mission_id, source, intent_level, intent_score, email, phone FROM leads WHERE id=?", (int(lead_id),))
            return cursor.fetchone()

    def _get_attempt(self, attempt_id: int) -> Any:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, lead_id, experiment_id, service_type, tier, offer_payload_json, proposed_price, status FROM conversion_attempts WHERE id=?", (int(attempt_id),))
            return cursor.fetchone()

    def _build_value_summary(self, service_type: str, tier: str, expected_outcome: str) -> str:
        return f"{service_type.replace('_', ' ').title()} ({tier.title()}) focused on {expected_outcome.lower()}."

    def _build_offer_message(self, offer: Dict[str, Any]) -> str:
        deliverables = offer.get("deliverables") or []
        return (
            f"Proposed Offer: {offer.get('service_type')} - {offer.get('tier')}\n"
            f"Expected outcome: {offer.get('expected_outcome')}\n"
            f"Deliverables:\n" + "\n".join([f"- {d}" for d in deliverables]) + "\n"
            f"Proposed price: ${(offer.get('pricing') or {}).get('final_price')}\n"
            f"Value: {offer.get('value_summary')}"
        )
