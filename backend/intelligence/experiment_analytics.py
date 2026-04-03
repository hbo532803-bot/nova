from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.database import get_db


class ExperimentAnalytics:
    """
    Analytics layer over experiment tables:
    - success scoring (based on validation_score + metrics)
    - ROI estimation
    - trend detection across experiments (recent vs older)
    """

    def summary(self, *, limit: int = 50) -> Dict[str, Any]:
        experiments = self._recent_experiments(limit=limit)
        if not experiments:
            return {"experiments": 0, "success_rate": 0.0, "avg_roi": 0.0, "trend": "flat"}

        success = [
            e
            for e in experiments
            if str(e.get("status")) in ("TESTING", "LIVE", "SCALING", "SUCCEEDED", "SUCCESS")
            and float(e.get("validation_score") or 0) >= 60
        ]
        success_rate = len(success) / max(1, len(experiments))
        rois = [float(self._roi_estimate(e)) for e in experiments]
        avg_roi = sum(rois) / max(1, len(rois)) if rois else 0.0

        mid = max(1, len(experiments) // 2)
        recent = experiments[:mid]
        older = experiments[mid:]
        recent_avg = self._avg_validation(recent)
        older_avg = self._avg_validation(older)
        if recent_avg > older_avg + 5:
            trend = "up"
        elif recent_avg < older_avg - 5:
            trend = "down"
        else:
            trend = "flat"

        return {
            "experiments": len(experiments),
            "success_rate": round(success_rate, 3),
            "avg_roi": round(avg_roi, 4),
            "trend": trend,
            "recent_avg_validation": recent_avg,
            "older_avg_validation": older_avg,
        }

    def list(self, *, limit: int = 50) -> List[Dict[str, Any]]:
        experiments = self._recent_experiments(limit=limit)
        out: List[Dict[str, Any]] = []
        for e in experiments:
            exp_id = int(e.get("id") or 0)
            metric_bundle = self._metric_bundle(exp_id)
            out.append(
                {
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "status": e.get("status"),
                    "validation_score": float(e.get("validation_score") or 0),
                    "roi": float(self._roi_estimate(e)),
                    "capital_allocated": float(e.get("capital_allocated") or 0),
                    "success_score": self._success_score(e),
                    "last_tested": str(e.get("last_tested") or ""),
                    "signals": metric_bundle,
                }
            )
        return out

    def _success_score(self, e: Dict[str, Any]) -> float:
        v = float(e.get("validation_score") or 0)
        roi = float(self._roi_estimate(e))
        return round(min(100.0, max(0.0, (0.7 * v) + (0.3 * (roi * 100.0)))), 2)

    def _roi_estimate(self, e: Dict[str, Any]) -> float:
        # Prefer stored roi if present and non-zero-ish, else estimate from revenue/cost.
        try:
            roi = float(e.get("roi") or 0)
            if roi != 0:
                return roi
        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in experiment_analytics.py")

        revenue = float(e.get("revenue_generated") or 0)
        cost = float(e.get("cost_incurred") or 0)
        if cost <= 0:
            return 0.0
        return (revenue - cost) / cost

    def _recent_experiments(self, *, limit: int) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM economic_experiments ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def _metric_bundle(self, experiment_id: int) -> Dict[str, Any]:
        """
        Aggregates recent metric signals into a compact bundle.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT metric_key, AVG(metric_value) as avg_v, MAX(metric_value) as max_v
                FROM experiment_metrics
                WHERE experiment_id = ?
                GROUP BY metric_key
                """,
                (experiment_id,),
            )
            rows = cursor.fetchall()
        bundle = {}
        for r in rows:
            k = str(r["metric_key"])
            bundle[k] = {"avg": float(r["avg_v"] or 0), "max": float(r["max_v"] or 0)}
        return bundle

    def _avg_validation(self, rows: List[Dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        vals = [float(r.get("validation_score") or 0) for r in rows]
        return round(sum(vals) / max(1, len(vals)), 2)

