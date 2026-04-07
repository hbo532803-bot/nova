from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from backend.database import get_db
from backend.system.audit_log import audit_log


class SignalEngine:
    """
    Reliable signal tracking for real/simulated execution telemetry.
    """

    VALID_EVENTS = {"page_view", "click", "lead", "payment"}
    VALID_DATA_SOURCES = {"real", "simulated"}
    VALID_TRAFFIC_SOURCES = {"organic", "manual", "ads", "unknown"}
    VALID_LEAD_QUALITY = {"high", "medium", "low"}

    def track_event(
        self,
        *,
        event_type: str,
        mission_id: str,
        source: str,
        experiment_id: int | None = None,
        session_id: str | None = None,
        event_value: float | None = None,
        is_simulated: bool = False,
        data_source: str | None = None,
        traffic_source: str = "unknown",
        lead_quality: str | None = None,
        conversion_to_payment: bool | None = None,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = (event_type or "").strip().lower()
        if event not in self.VALID_EVENTS:
            raise ValueError(f"unsupported event_type: {event_type}")
        if not mission_id:
            raise ValueError("mission_id is required")

        resolved_data_source = (data_source or ("simulated" if is_simulated else "real")).strip().lower()
        if resolved_data_source not in self.VALID_DATA_SOURCES:
            raise ValueError("data_source must be real|simulated")
        simulated_flag = resolved_data_source == "simulated"

        resolved_traffic = (traffic_source or "unknown").strip().lower()
        if resolved_traffic not in self.VALID_TRAFFIC_SOURCES:
            resolved_traffic = "unknown"

        resolved_lead_quality = None
        if lead_quality is not None:
            lq = str(lead_quality).strip().lower()
            if lq not in self.VALID_LEAD_QUALITY:
                raise ValueError("lead_quality must be high|medium|low")
            resolved_lead_quality = lq

        sid = (session_id or "").strip() or f"anon-{uuid.uuid4().hex[:10]}"
        payload = metadata or {}
        now = datetime.utcnow()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO real_signal_events
                (mission_id, experiment_id, event_type, source, session_id, event_value, is_simulated, reason, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    int(experiment_id) if experiment_id is not None else None,
                    event,
                    source,
                    sid,
                    float(event_value) if event_value is not None else None,
                    1 if simulated_flag else 0,
                    reason.strip() or None,
                    json.dumps(
                        {
                            **payload,
                            "data_source": resolved_data_source,
                            "traffic_source": resolved_traffic,
                            "lead_quality": resolved_lead_quality,
                            "conversion_to_payment": conversion_to_payment,
                        }
                    ),
                    now,
                ),
            )
            signal_id = int(cursor.lastrowid)

            cursor.execute(
                "SELECT COALESCE(MAX(event_sequence),0) AS n FROM session_journey WHERE mission_id=? AND session_id=?",
                (mission_id, sid),
            )
            next_seq = int(cursor.fetchone()["n"] or 0) + 1
            cursor.execute(
                """
                INSERT INTO session_journey
                (mission_id, experiment_id, session_id, event_sequence, event_type, data_source, traffic_source, lead_quality, conversion_to_payment, event_value, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    int(experiment_id) if experiment_id is not None else None,
                    sid,
                    next_seq,
                    event,
                    resolved_data_source,
                    resolved_traffic,
                    resolved_lead_quality,
                    1 if conversion_to_payment is True else (0 if conversion_to_payment is False else None),
                    float(event_value) if event_value is not None else None,
                    json.dumps(payload),
                    now,
                ),
            )
            conn.commit()

        audit_log(
            actor=None,
            action="signal.track",
            target=mission_id,
            payload={
                "signal_id": signal_id,
                "event": event,
                "source": source,
                "experiment_id": experiment_id,
                "data_source": resolved_data_source,
                "traffic_source": resolved_traffic,
                "sequence": next_seq,
                "reason": reason,
            },
        )

        return {
            "ok": True,
            "signal_id": signal_id,
            "event_type": event,
            "mission_id": mission_id,
            "session_id": sid,
            "event_sequence": next_seq,
            "data_source": resolved_data_source,
            "traffic_source": resolved_traffic,
        }

    def safe_track_event(self, **kwargs) -> None:
        try:
            self.track_event(**kwargs)
        except Exception:
            logging.getLogger(__name__).warning("signal tracking failed", exc_info=True)
