from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from backend.database import get_db
from backend.intelligence.experiment_analytics import ExperimentAnalytics


@dataclass(frozen=True)
class LifecycleDecision:
    experiment_id: int
    action: str  # "SCALE" | "TERMINATE" | "HOLD"
    reason: str
    new_status: str | None = None
    capital_delta: float = 0.0


class ExperimentLifecycleEngine:
    """
    Portfolio lifecycle automation (executed via action spine):
    - detect successful experiments and scale
    - terminate failing experiments early
    - portfolio balance hints (best-effort)
    """

    def evaluate_portfolio(self, *, limit: int = 50) -> Dict[str, Any]:
        analytics = ExperimentAnalytics()
        items = analytics.list(limit=limit)

        decisions: List[LifecycleDecision] = []
        for e in items:
            exp_id = int(e.get("id") or 0)
            status = str(e.get("status") or "")
            score = float(e.get("success_score") or 0)
            roi = float(e.get("roi") or 0)
            cap = float(e.get("capital_allocated") or 0)

            # Early terminate: repeated failure states or very low score with ROI < 0
            if status in ("FAILED", "ARCHIVED", "TERMINATED"):
                decisions.append(LifecycleDecision(exp_id, "HOLD", "already_inactive"))
                continue

            if score < 35 and roi < 0:
                decisions.append(LifecycleDecision(exp_id, "TERMINATE", "low_score_negative_roi", new_status="FAILED"))
                continue

            # Scale: high score + positive ROI
            if score >= 75 and roi > 0.2:
                delta = max(50.0, cap * 0.25) if cap > 0 else 100.0
                decisions.append(LifecycleDecision(exp_id, "SCALE", "high_score_positive_roi", new_status="SCALING", capital_delta=delta))
                continue

            # Promote: stage/lifecycle success without scaling yet
            if score >= 65 and status == "TESTING":
                decisions.append(LifecycleDecision(exp_id, "HOLD", "promising_testing", new_status="LIVE"))
                continue

            decisions.append(LifecycleDecision(exp_id, "HOLD", "no_change"))

        return {
            "summary": analytics.summary(limit=limit),
            "decisions": [d.__dict__ for d in decisions],
        }

    def apply_decisions(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        now = datetime.utcnow()
        applied = []
        with get_db() as conn:
            cursor = conn.cursor()
            for d in decisions:
                exp_id = int(d.get("experiment_id") or 0)
                action = str(d.get("action") or "")
                new_status = d.get("new_status")
                delta = float(d.get("capital_delta") or 0.0)

                if action == "TERMINATE" and new_status:
                    cursor.execute(
                        "UPDATE economic_experiments SET status=?, last_tested=?, notes=? WHERE id=?",
                        (new_status, now, "lifecycle:terminated", exp_id),
                    )
                    applied.append({"experiment_id": exp_id, "action": action, "status": new_status})

                if action == "SCALE":
                    if new_status:
                        cursor.execute("UPDATE economic_experiments SET status=? WHERE id=?", (new_status, exp_id))
                    cursor.execute(
                        "UPDATE economic_experiments SET capital_allocated = capital_allocated + ?, last_tested=?, notes=? WHERE id=?",
                        (delta, now, "lifecycle:scaled", exp_id),
                    )
                    applied.append({"experiment_id": exp_id, "action": action, "delta": delta, "status": new_status})

                if action == "HOLD" and new_status:
                    cursor.execute(
                        "UPDATE economic_experiments SET status=?, last_tested=?, notes=? WHERE id=?",
                        (new_status, now, "lifecycle:promoted", exp_id),
                    )
                    applied.append({"experiment_id": exp_id, "action": action, "status": new_status})

            conn.commit()
        return {"ok": True, "applied": applied}

