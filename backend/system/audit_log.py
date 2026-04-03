from __future__ import annotations

import json
from typing import Any, Optional

from backend.db_retry import run_db_write_with_retry
from backend.system.observability import get_request_id, get_actor


def audit_log(
    *,
    actor: Optional[str],
    action: str,
    target: Optional[str] = None,
    payload: Any = None,
    ip: Optional[str] = None,
) -> None:
    """
    Best-effort audit log. Never raises (production stability).
    """
    try:
        payload_text = None
        if payload is not None:
            try:
                payload_text = json.dumps(payload)
            except Exception:
                payload_text = str(payload)

        rid = get_request_id()
        actor_value = actor if actor is not None else get_actor()
        if rid:
            payload_text = json.dumps({"request_id": rid, "payload": payload_text})

        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_log (actor, action, target, payload, ip)
                VALUES (?, ?, ?, ?, ?)
                """,
                (actor_value, action, target, payload_text, ip),
            )
            conn.commit()
            return None

        run_db_write_with_retry("audit_log.insert", _write)
    except Exception:
        return

