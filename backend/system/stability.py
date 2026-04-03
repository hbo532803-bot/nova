from __future__ import annotations

import datetime
from typing import Any, Dict, List

from backend.database import get_db
from backend.frontend_api.event_bus import broadcast
from backend.system.state_store import StateStore
from backend.system.validation import validate_architecture


class SystemStability:
    """
    System stability layer:
    - health monitoring (best-effort checks)
    - recovery tools for partial execution and inconsistent states
    """

    def health(self) -> Dict[str, Any]:
        state = StateStore().get()
        arch = validate_architecture()
        stuck = self._stuck_commands(minutes=30)
        return {
            "state": state.__dict__,
            "architecture_ok": bool(arch.get("ok")),
            "architecture": arch,
            "stuck_commands": stuck,
            "ok": bool(arch.get("ok")) and state.state != "ERROR",
        }

    def recover(self) -> Dict[str, Any]:
        """
        Conservative recovery:
        - mark long-running RUNNING commands as FAILED
        - if system state is ERROR, return it to IDLE
        """
        now = datetime.datetime.utcnow()
        stuck = self._stuck_commands(minutes=30)

        with get_db() as conn:
            cursor = conn.cursor()
            for c in stuck:
                cursor.execute(
                    """
                    UPDATE nova_commands
                    SET status='FAILED', result=?, updated_at=?
                    WHERE id=?
                    """,
                    ("recovered:stuck_running", now, int(c["id"])),
                )
            conn.commit()

        state_store = StateStore()
        snap = state_store.get()
        recovered_state = None
        if snap.state == "ERROR":
            recovered_state = state_store.set("IDLE", last_error=None).__dict__

        broadcast({"type": "log", "level": "warn", "message": f"Stability recovery executed stuck={len(stuck)}"})
        return {"ok": True, "stuck_marked_failed": len(stuck), "recovered_state": recovered_state}

    def _stuck_commands(self, *, minutes: int) -> List[Dict[str, Any]]:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, command_text, status, created_at, updated_at
                FROM nova_commands
                WHERE status='RUNNING'
                """,
            )
            rows = [dict(r) for r in cursor.fetchall()]

        stuck = []
        for r in rows:
            # updated_at may be null; fallback to created_at
            ts = r.get("updated_at") or r.get("created_at")
            try:
                # SQLite returns strings; best-effort parse
                dt = datetime.datetime.fromisoformat(str(ts)) if ts else None
            except Exception:
                dt = None
            if dt and dt < cutoff:
                stuck.append(r)
        return stuck

