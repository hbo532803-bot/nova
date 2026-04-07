from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from backend.database import get_db
from backend.intelligence.metrics_engine import MetricsEngine


@dataclass(frozen=True)
class PriorityWeights:
    profit: float = 0.4
    roi: float = 0.3
    growth_rate: float = 0.2
    reliability: float = 0.1


class ProfitIntelligenceEngine:
    """
    Profit-first intelligence layer:
    - tracks cost signals
    - computes profit/ROI/CAC
    - compares experiments and ranks by economics + reliability
    - derives priority labels for capital allocation
    """

    def __init__(self) -> None:
        self.metrics = MetricsEngine()
        self.weights = PriorityWeights()

    def track_cost(
        self,
        experiment_id: int,
        amount: float,
        *,
        source: str = "manual_input",
        is_simulated: bool = False,
        metadata_json: str | None = None,
    ) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO experiment_cost_events (experiment_id, source, cost_amount, is_simulated, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (int(experiment_id), str(source), float(amount), 1 if is_simulated else 0, metadata_json),
            )
            conn.commit()
        return {"ok": True, "experiment_id": int(experiment_id), "amount": float(amount), "source": source}

    def update_profit_snapshot(self, experiment_id: int) -> Dict[str, Any]:
        metrics = self.metrics.compute(experiment_id=int(experiment_id))
        real = metrics.get("real") or {}
        simulated = metrics.get("simulated") or {}
        reliability = metrics.get("reliability") or {}

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN is_simulated=0 THEN cost_amount ELSE 0 END),0) AS real_cost,
                    COALESCE(SUM(CASE WHEN is_simulated=1 THEN cost_amount ELSE 0 END),0) AS simulated_cost
                FROM experiment_cost_events
                WHERE experiment_id=?
                """,
                (int(experiment_id),),
            )
            cost_row = cursor.fetchone()

            cursor.execute("SELECT COALESCE(SUM(amount),0) AS revenue FROM revenue_events WHERE mission_id=?", (str(experiment_id),))
            revenue_row = cursor.fetchone()
            revenue_from_events = float((revenue_row["revenue"] or 0.0) if revenue_row else 0.0)

            cursor.execute(
                """
                SELECT COALESCE(revenue_generated,0) AS revenue_generated
                FROM economic_experiments
                WHERE id=?
                """,
                (int(experiment_id),),
            )
            exp_row = cursor.fetchone()

            base_revenue = float((exp_row["revenue_generated"] or 0.0) if exp_row else 0.0)
            revenue_total = max(base_revenue, revenue_from_events, float(metrics.get("metrics", {}).get("paid_revenue") or 0.0))
            real_cost = float((cost_row["real_cost"] or 0.0) if cost_row else 0.0)
            simulated_cost = float((cost_row["simulated_cost"] or 0.0) if cost_row else 0.0)
            cost_total = real_cost + simulated_cost

            total_clicks = int(real.get("clicks") or 0) + int(simulated.get("clicks") or 0)
            total_leads = int(real.get("leads") or 0) + int(simulated.get("leads") or 0)
            real_users = int(real.get("unique_users") or 0)
            acquisitions = int(real.get("payments") or 0)

            cost_per_click = (cost_total / total_clicks) if total_clicks else 0.0
            cost_per_lead = (cost_total / total_leads) if total_leads else 0.0
            profit = revenue_total - real_cost
            profit_per_user = (profit / real_users) if real_users else 0.0
            cac = (real_cost / acquisitions) if acquisitions else 0.0
            roi = (profit / real_cost) if real_cost > 0 else 0.0

            windows = self._time_windows(cursor, int(experiment_id))
            growth_rate = windows["growth_rate"]

            cursor.execute(
                """
                UPDATE economic_experiments
                SET
                    cost_total=?,
                    cost_real_total=?,
                    cost_simulated_total=?,
                    cost_per_click=?,
                    cost_per_lead=?,
                    revenue_total=?,
                    profit_total=?,
                    profit_per_user=?,
                    cac=?,
                    roi=?,
                    growth_rate=?
                WHERE id=?
                """,
                (
                    cost_total,
                    real_cost,
                    simulated_cost,
                    cost_per_click,
                    cost_per_lead,
                    revenue_total,
                    profit,
                    profit_per_user,
                    cac,
                    roi,
                    growth_rate,
                    int(experiment_id),
                ),
            )
            conn.commit()

        return {
            "experiment_id": int(experiment_id),
            "cost": {
                "total": round(cost_total, 4),
                "real": round(real_cost, 4),
                "simulated": round(simulated_cost, 4),
                "cost_per_click": round(cost_per_click, 4),
                "cost_per_lead": round(cost_per_lead, 4),
            },
            "revenue_total": round(revenue_total, 4),
            "profit": round(profit, 4),
            "profit_per_user": round(profit_per_user, 4),
            "cac": round(cac, 4),
            "roi": round(roi, 4),
            "growth_rate": round(growth_rate, 4),
            "time_windows": windows,
            "reliability": reliability,
        }

    def compare_experiments(self, *, limit: int = 100) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id
                FROM economic_experiments
                WHERE status NOT IN ('FAILED', 'ARCHIVED')
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            exp_ids = [int(r["id"]) for r in cursor.fetchall()]

        ranking: List[Dict[str, Any]] = []
        for exp_id in exp_ids:
            snap = self.update_profit_snapshot(exp_id)
            rel = snap.get("reliability") or {}
            metrics = self.metrics.compute(experiment_id=exp_id).get("metrics") or {}
            conversion = float(metrics.get("conversion_rate") or 0.0)
            roi = float(snap.get("roi") or 0.0)
            profit = float(snap.get("profit") or 0.0)
            reliability_score = 1.0 if bool(rel.get("is_data_reliable")) else 0.0
            score = (conversion * 0.25) + (max(-1.0, min(2.0, roi)) * 0.35) + ((profit / 1000.0) * 0.25) + (reliability_score * 0.15)
            ranking.append(
                {
                    "experiment_id": exp_id,
                    "conversion_rate": round(conversion, 4),
                    "profit": round(profit, 4),
                    "roi": round(roi, 4),
                    "reliability": reliability_score,
                    "score": round(score, 4),
                }
            )

        ranking.sort(key=lambda x: x["score"], reverse=True)
        return {"best_experiment": ranking[0]["experiment_id"] if ranking else None, "ranking": ranking}

    def update_priority(self, experiment_id: int) -> Dict[str, Any]:
        snap = self.update_profit_snapshot(experiment_id)
        reliability = 1.0 if bool((snap.get("reliability") or {}).get("is_data_reliable")) else 0.0
        profit = float(snap.get("profit") or 0.0)
        roi = float(snap.get("roi") or 0.0)
        growth = float(snap.get("growth_rate") or 0.0)

        normalized_profit = max(0.0, min(1.0, profit / 1000.0))
        normalized_roi = max(0.0, min(1.0, roi))
        normalized_growth = max(0.0, min(1.0, (growth + 1.0) / 2.0))
        score = (
            normalized_profit * self.weights.profit
            + normalized_roi * self.weights.roi
            + normalized_growth * self.weights.growth_rate
            + reliability * self.weights.reliability
        )

        if not bool((snap.get("reliability") or {}).get("is_data_reliable")):
            level = "LOW"
        elif roi <= 0:
            level = "LOW"
        elif score >= 0.7:
            level = "HIGH"
        elif score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE economic_experiments SET priority_score=?, priority_level=? WHERE id=?",
                (score, level, int(experiment_id)),
            )
            conn.commit()

        return {"experiment_id": int(experiment_id), "priority_score": round(score, 4), "priority_level": level}

    def _time_windows(self, cursor: Any, experiment_id: int) -> Dict[str, float]:
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount),0) AS v
            FROM revenue_events
            WHERE mission_id=? AND created_at >= datetime('now','-24 hours')
            """,
            (str(experiment_id),),
        )
        rev_24h = float((cursor.fetchone()["v"] or 0.0))
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount),0) AS v
            FROM revenue_events
            WHERE mission_id=? AND created_at >= datetime('now','-7 days')
            """,
            (str(experiment_id),),
        )
        rev_7d = float((cursor.fetchone()["v"] or 0.0))

        cursor.execute(
            """
            SELECT COALESCE(SUM(cost_amount),0) AS v
            FROM experiment_cost_events
            WHERE experiment_id=? AND is_simulated=0 AND created_at >= datetime('now','-24 hours')
            """,
            (int(experiment_id),),
        )
        cost_24h = float((cursor.fetchone()["v"] or 0.0))
        cursor.execute(
            """
            SELECT COALESCE(SUM(cost_amount),0) AS v
            FROM experiment_cost_events
            WHERE experiment_id=? AND is_simulated=0 AND created_at >= datetime('now','-7 days')
            """,
            (int(experiment_id),),
        )
        cost_7d = float((cursor.fetchone()["v"] or 0.0))

        profit_24h = rev_24h - cost_24h
        profit_7d = rev_7d - cost_7d
        avg_daily_7d = profit_7d / 7.0 if profit_7d else 0.0
        growth_rate = ((profit_24h - avg_daily_7d) / abs(avg_daily_7d)) if avg_daily_7d else (1.0 if profit_24h > 0 else 0.0)
        return {
            "last_24h_profit": round(profit_24h, 4),
            "last_7_days_profit": round(profit_7d, 4),
            "growth_rate": round(growth_rate, 4),
        }
