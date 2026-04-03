from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.database import get_db


class ExperimentMetricsStore:
    def record(self, experiment_id: int, metric_key: str, metric_value: float, *, source: str = "runner") -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO experiment_metrics (experiment_id, metric_key, metric_value, source)
                VALUES (?, ?, ?, ?)
                """,
                (experiment_id, metric_key, float(metric_value), source),
            )
            conn.commit()

    def list_recent(self, experiment_id: int, *, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, experiment_id, metric_key, metric_value, source, created_at
                FROM experiment_metrics
                WHERE experiment_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (experiment_id, limit),
            )
            rows = cursor.fetchall()
        return [dict(r) for r in rows]

