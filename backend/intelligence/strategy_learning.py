from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from backend.database import get_db
from backend.intelligence.experiment_analytics import ExperimentAnalytics
from backend.knowledge.graph_store import KnowledgeGraphStore
from backend.intelligence.profit_intelligence_engine import ProfitIntelligenceEngine


@dataclass(frozen=True)
class StrategyAdjustment:
    key: str
    value: Any
    reason: str


class StrategyLearningEngine:
    """
    Minimal strategy learning layer:
    - detect patterns from outcomes (reflections + experiment metrics)
    - persist small strategy adjustments into system_settings
    """

    SETTINGS_KEY = "strategy_adjustments"

    def __init__(self) -> None:
        self.profit_engine = ProfitIntelligenceEngine()

    def learn(self, *, lookback: int = 100) -> Dict[str, Any]:
        reflections = self._recent_reflections(limit=lookback)

        # Cross-experiment trends (cluster analysis)
        exp_trends = self._experiment_trends(limit=min(200, max(20, lookback)))
        long_term = self._long_term_trends()
        feedback = self._feedback_summary(limit=min(200, max(20, lookback)))
        if not reflections:
            adjustments = [StrategyAdjustment("risk_bias", "NEUTRAL", "no_reflections")]
            return self._persist(adjustments, meta={"experiments": exp_trends, "long_term": long_term, "feedback": feedback})

        failures = sum(1 for r in reflections if not bool(r.get("success")))
        failure_rate = failures / max(1, len(reflections))

        adjustments: List[StrategyAdjustment] = []
        if failure_rate >= 0.6:
            adjustments.append(StrategyAdjustment("risk_bias", "LOW", "high_failure_rate"))
            adjustments.append(StrategyAdjustment("autonomy_bias", "HUMAN_APPROVAL", "high_failure_rate"))
        elif failure_rate <= 0.2:
            adjustments.append(StrategyAdjustment("risk_bias", "HIGH", "low_failure_rate"))
            adjustments.append(StrategyAdjustment("autonomy_bias", "LIMITED_AUTONOMY", "low_failure_rate"))
        else:
            adjustments.append(StrategyAdjustment("risk_bias", "NEUTRAL", "moderate_failure_rate"))

        # Adaptive strategy selection (very simple policy)
        if exp_trends.get("trend") == "down":
            adjustments.append(StrategyAdjustment("exploration_mode", True, "experiment_trend_down"))
        if exp_trends.get("trend") == "up":
            adjustments.append(StrategyAdjustment("exploration_mode", False, "experiment_trend_up"))

        # Adaptive experiment selection hint (playbook preference)
        if feedback.get("gather_more_data_rate", 0.0) >= 0.5:
            adjustments.append(StrategyAdjustment("data_collection_bias", "INCREASE_TRAFFIC", "reliability_insufficient"))
        if feedback.get("scale_rate", 0.0) >= 0.4:
            adjustments.append(StrategyAdjustment("execution_bias", "AGGRESSIVE_SCALE", "feedback_scale_rate_high"))
        elif feedback.get("fail_rate", 0.0) >= 0.5:
            adjustments.append(StrategyAdjustment("execution_bias", "SAFE_OPTIMIZE", "feedback_fail_rate_high"))

        best_cluster = str(exp_trends.get("best_cluster") or "")
        if best_cluster and best_cluster != "unknown":
            preferred = self._preferred_playbooks_for_cluster(best_cluster)
            if preferred:
                adjustments.append(StrategyAdjustment("preferred_playbooks", preferred, "best_cluster"))
                self._record_strategy_pattern(best_cluster)

        return self._persist(
            adjustments,
            meta={
                "failure_rate": failure_rate,
                "count": len(reflections),
                "experiments": exp_trends,
                "long_term": long_term,
                "feedback": feedback,
            },
        )

    def _recent_reflections(self, *, limit: int) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, input_objective, success, confidence_before, confidence_after, created_at
                FROM reflections
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def _experiment_trends(self, *, limit: int = 50) -> Dict[str, Any]:
        """
        Cross-experiment trend detection:
        - uses ExperimentAnalytics summary
        - clusters experiments by experiment_type and reports avg success_score
        """
        analytics = ExperimentAnalytics()
        summary = analytics.summary(limit=limit)
        items = analytics.list(limit=limit)

        clusters: Dict[str, list[float]] = {}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, experiment_type FROM economic_experiments ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            et = {int(r["id"]): str(r["experiment_type"] or "unknown") for r in cursor.fetchall()}

        for e in items:
            cid = et.get(int(e.get("id") or 0), "unknown")
            clusters.setdefault(cid, []).append(float(e.get("success_score") or 0))

        cluster_avgs = {k: round(sum(v) / max(1, len(v)), 2) for k, v in clusters.items()}
        best_cluster = max(cluster_avgs.items(), key=lambda x: x[1])[0] if cluster_avgs else "unknown"

        return {
            **summary,
            "clusters": cluster_avgs,
            "best_cluster": best_cluster,
        }

    def _long_term_trends(self) -> Dict[str, Any]:
        """
        Long-term trend detection (bounded):
        - compares last 30 vs previous 30 experiments validation/success score
        - emits a trend classification used for strategy selection
        """
        analytics = ExperimentAnalytics()
        items = analytics.list(limit=60)
        if len(items) < 10:
            return {"trend": "insufficient_data", "recent_avg_success": 0.0, "older_avg_success": 0.0}

        recent = items[:30]
        older = items[30:60]
        r = sum(float(x.get("success_score") or 0) for x in recent) / max(1, len(recent))
        o = sum(float(x.get("success_score") or 0) for x in older) / max(1, len(older))

        if r > o + 5:
            trend = "up"
        elif r < o - 5:
            trend = "down"
        else:
            trend = "flat"

        return {"trend": trend, "recent_avg_success": round(r, 2), "older_avg_success": round(o, 2)}

    def _feedback_summary(self, *, limit: int = 100) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT decision, COUNT(*) AS n
                FROM experiment_feedback_loops
                GROUP BY decision
                ORDER BY n DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT COUNT(*) AS n
                FROM experiment_feedback_loops
                WHERE reason='insufficient_reliable_sample'
                """
            )
            unreliable = int((cursor.fetchone()["n"] or 0))

        totals = {str(r["decision"] or "unknown").lower(): int(r["n"] or 0) for r in rows}
        total = max(1, sum(totals.values()))
        return {
            "counts": totals,
            "scale_rate": round(totals.get("scale", 0) / total, 3),
            "fail_rate": round(totals.get("fail", 0) / total, 3),
            "gather_more_data_rate": round(totals.get("gather_more_data", 0) / total, 3),
            "unreliable_decisions": unreliable,
        }

    def _preferred_playbooks_for_cluster(self, cluster: str) -> list[str]:
        """
        Best-effort mapping from experiment_type cluster to playbook templates.
        """
        c = cluster.lower()
        if "landing" in c or "conversion" in c:
            return ["landing_page_validation", "marketing_funnel_test"]
        if "content" in c:
            return ["content_growth_loop", "content_growth"]
        if "saas" in c or "prototype" in c:
            return ["saas_prototype_experiment", "saas_validation"]
        return []

    def _persist(self, adjustments: List[StrategyAdjustment], meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = {
            "updated_at": datetime.utcnow().isoformat(),
            "meta": meta or {},
            "adjustments": [{"key": a.key, "value": a.value, "reason": a.reason} for a in adjustments],
        }
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                (self.SETTINGS_KEY, json.dumps(payload)),
            )
            conn.commit()
        try:
            kg = KnowledgeGraphStore()
            kg.upsert_node("strategy", "current", payload)
            best = (meta or {}).get("experiments", {}).get("best_cluster") if meta else None
            if best:
                kg.upsert_node("experiment_cluster", str(best), {"label": str(best)})
                kg.add_edge("strategy", "current", "FAVORS_CLUSTER", "experiment_cluster", str(best))
        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in strategy_learning.py")
        return {"ok": True, "strategy": payload}

    def _record_strategy_pattern(self, strategy_type: str) -> None:
        comparison = self.profit_engine.compare_experiments(limit=100)
        ranking = comparison.get("ranking") or []
        if not ranking:
            return
        profitable = [x for x in ranking if float(x.get("profit") or 0.0) > 0]
        success_rate = len(profitable) / max(1, len(ranking))
        avg_profit = sum(float(x.get("profit") or 0.0) for x in ranking) / max(1, len(ranking))
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO strategy_patterns (strategy_type, success_rate, avg_profit, sample_size, last_seen)
                VALUES (?, ?, ?, ?, datetime('now'))
                ON CONFLICT(strategy_type) DO UPDATE SET
                    success_rate=excluded.success_rate,
                    avg_profit=excluded.avg_profit,
                    sample_size=excluded.sample_size,
                    last_seen=datetime('now')
                """,
                (strategy_type, success_rate, avg_profit, len(ranking)),
            )
            conn.commit()
