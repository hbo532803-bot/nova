from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from backend.database import get_db
from backend.system.audit_log import audit_log


class SignalEngine:
    """
    Real capability signal tracking.

    Stores all user/market execution signals with explicit simulation markers.
    """

    VALID_EVENTS = {"page_view", "click", "lead", "payment"}

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
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = (event_type or "").strip().lower()
        if event not in self.VALID_EVENTS:
            raise ValueError(f"unsupported event_type: {event_type}")
        if not mission_id:
            raise ValueError("mission_id is required")

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
                    (session_id or "").strip() or None,
                    float(event_value) if event_value is not None else None,
                    1 if is_simulated else 0,
                    reason.strip() or None,
                    json.dumps(payload),
                    now,
                ),
            )
            signal_id = int(cursor.lastrowid)
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
                "is_simulated": bool(is_simulated),
                "reason": reason,
            },
        )

        return {
            "ok": True,
            "signal_id": signal_id,
            "event_type": event,
            "mission_id": mission_id,
            "is_simulated": bool(is_simulated),
        }

    def safe_track_event(self, **kwargs) -> None:
        try:
            self.track_event(**kwargs)
        except Exception:
            logging.getLogger(__name__).warning("signal tracking failed", exc_info=True)
