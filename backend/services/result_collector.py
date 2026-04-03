from __future__ import annotations

import ast
import json
from typing import Any

from backend.database import get_db
from backend.memory.working_memory import WorkingMemoryStore


class ResultCollector:
    """
    Collects task outputs by mission_id (or order_id when resolvable).
    Uses existing working_memory and command history tables only.
    """

    def __init__(self):
        self.memory = WorkingMemoryStore()

    def store_task_output(self, mission_id: str, key: str, output: Any) -> None:
        if not mission_id:
            return
        try:
            self.memory.put_json(mission_id, key, {"output": output})
        except Exception:
            # best effort; execution path must not be blocked
            pass

    def collect_outputs(self, *, mission_id: str | None = None, order_id: str | None = None) -> dict[str, Any]:
        resolved_mission_id = mission_id or self._resolve_mission_id(order_id)
        if not resolved_mission_id:
            return {
                "mission_id": mission_id,
                "order_id": order_id,
                "task_outputs": [],
                "meta": {"found": False},
            }

        rows = self.memory.list(resolved_mission_id, limit=500)
        items: list[dict[str, Any]] = []

        for row in rows:
            key = str(row.get("key") or "")
            if not key.startswith("action:") and ":execution" not in key:
                continue
            parsed = self._safe_parse(row.get("value"))
            output = parsed.get("output") if isinstance(parsed, dict) and "output" in parsed else parsed
            items.append(
                {
                    "key": key,
                    "output": output,
                    "created_at": row.get("created_at"),
                }
            )

        return {
            "mission_id": resolved_mission_id,
            "order_id": order_id,
            "task_outputs": list(reversed(items)),
            "meta": {
                "found": len(items) > 0,
                "task_count": len(items),
            },
        }

    def _resolve_mission_id(self, order_id: str | None) -> str | None:
        if not order_id:
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT result FROM nova_commands WHERE id = ?", (order_id,))
            row = cursor.fetchone()

        if not row or not row["result"]:
            return None

        payload = self._safe_parse(row["result"])
        if isinstance(payload, dict):
            if payload.get("mission_id"):
                return str(payload["mission_id"])
            decision = payload.get("decision") or {}
            if isinstance(decision, dict) and decision.get("mission_id"):
                return str(decision["mission_id"])
        return None

    @staticmethod
    def _safe_parse(raw: Any) -> Any:
        if isinstance(raw, (dict, list)):
            return raw
        text = str(raw or "").strip()
        if not text:
            return {}
        for parser in (json.loads, ast.literal_eval):
            try:
                return parser(text)
            except Exception:
                continue
        return text
