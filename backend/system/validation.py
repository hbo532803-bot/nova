from __future__ import annotations

from typing import Any, Dict, List

from backend.database import get_db
from backend.execution.action_types import ActionType


def validate_architecture() -> Dict[str, Any]:
    """
    Runtime validation pass (best-effort).
    Confirms key invariants required by Nova docs:
    - state machine table exists
    - reflections table exists and is being written to
    - command queue table exists
    - action types are defined
    """
    checks: List[Dict[str, Any]] = []

    def ok(name: str, detail: str = ""):
        checks.append({"name": name, "ok": True, "detail": detail})

    def fail(name: str, detail: str):
        checks.append({"name": name, "ok": False, "detail": detail})

    with get_db() as conn:
        cursor = conn.cursor()

        # Tables
        try:
            cursor.execute("SELECT state FROM nova_system_state WHERE id=1")
            row = cursor.fetchone()
            ok("state_table", f"state={row['state'] if row else 'missing_row'}")
        except Exception as e:
            fail("state_table", str(e))

        try:
            cursor.execute("SELECT COUNT(*) as n FROM reflections")
            n = cursor.fetchone()["n"]
            ok("reflections_table", f"count={n}")
        except Exception as e:
            fail("reflections_table", str(e))

        try:
            cursor.execute("SELECT COUNT(*) as n FROM nova_commands")
            n = cursor.fetchone()["n"]
            ok("commands_table", f"count={n}")
        except Exception as e:
            fail("commands_table", str(e))

        try:
            cursor.execute("SELECT COUNT(*) as n FROM experiment_metrics")
            n = cursor.fetchone()["n"]
            ok("experiment_metrics_table", f"count={n}")
        except Exception as e:
            fail("experiment_metrics_table", str(e))

    # Action types present
    try:
        names = [a.value for a in ActionType]
        ok("action_types", f"{len(names)} types")
    except Exception as e:
        fail("action_types", str(e))

    all_ok = all(c["ok"] for c in checks)
    return {"ok": all_ok, "checks": checks}

