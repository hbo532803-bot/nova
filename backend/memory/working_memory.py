from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.database import get_db
from backend.db_init import initialize_all_tables
from backend.db_retry import run_db_write_with_retry


class WorkingMemoryStore:
    """
    Shared working memory for agent teams (mission-scoped).
    This persists intermediate results so tasks can reuse them across nodes/cycles.
    """

    def ensure(self) -> None:
        initialize_all_tables(reset=False)

    def put(self, mission_id: str, key: str, value: str) -> None:
        self.ensure()
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO working_memory (mission_id, key, value) VALUES (?, ?, ?)",
                (mission_id, key, value),
            )
            conn.commit()
            return None

        run_db_write_with_retry("working_memory.insert", _write)

    def put_json(self, mission_id: str, key: str, value: Dict[str, Any]) -> None:
        self.put(mission_id, key, json.dumps(value))

    def list(self, mission_id: str, *, limit: int = 200) -> List[Dict[str, Any]]:
        self.ensure()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT key, value, created_at
                FROM working_memory
                WHERE mission_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (mission_id, limit),
            )
            rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def latest(self, mission_id: str, key: str) -> Optional[Dict[str, Any]]:
        self.ensure()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT value, created_at
                FROM working_memory
                WHERE mission_id = ? AND key = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (mission_id, key),
            )
            row = cursor.fetchone()
        if not row or not row["value"]:
            return None
        raw = str(row["value"])
        try:
            parsed = json.loads(raw)
            return {"value": parsed, "created_at": str(row["created_at"])}
        except Exception:
            return {"value": raw, "created_at": str(row["created_at"])}

