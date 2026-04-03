from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, List, Tuple

from backend.database import get_db


class KnowledgeGraphReasoner:
    """
    Derives insights from graph structures:
    - patterns across experiment outcomes
    - opportunity→experiment→strategy relationship analysis
    - reusable strategy discovery signals
    """

    def insights(self, *, limit_edges: int = 1000) -> Dict[str, Any]:
        edges = self._recent_edges(limit=limit_edges)

        # Outcome patterns
        outcome_counts = Counter()
        for e in edges:
            if e["relation"] == "HAS_OUTCOME" and e["target_type"] == "outcome":
                outcome_counts[e["target_key"]] += 1

        # Strategy relationships
        favors = [e for e in edges if e["source_type"] == "strategy" and e["relation"] == "FAVORS_CLUSTER"]
        discovered = [e for e in edges if e["source_type"] == "strategy" and e["relation"] == "DISCOVERED" and e["target_type"] == "opportunity"]

        # Opportunity→experiment→outcome chaining (best-effort using edges)
        launch_edges = [e for e in edges if e["relation"] == "LAUNCHED_EXPERIMENT"]
        exp_to_outcome = {e["source_key"]: e["target_key"] for e in edges if e["relation"] == "HAS_OUTCOME"}
        chain = []
        for le in launch_edges[:50]:
            exp_key = le["target_key"]
            chain.append(
                {
                    "opportunity": le["source_key"],
                    "experiment": exp_key,
                    "outcome": exp_to_outcome.get(exp_key),
                }
            )

        reusable = self._reusable_strategy_candidates()
        history = self._experiment_history_patterns(limit=60)

        return {
            "outcome_counts": dict(outcome_counts),
            "strategy_favors": favors[:20],
            "strategy_discovered_opportunities": len(discovered),
            "opportunity_experiment_outcome_samples": chain[:20],
            "reusable_strategies": reusable,
            "experiment_history_patterns": history,
        }

    def _recent_edges(self, *, limit: int) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_type, source_key, relation, target_type, target_key, weight, created_at
                FROM knowledge_edges
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def _reusable_strategy_candidates(self) -> List[Dict[str, Any]]:
        """
        Best-effort reusable strategy discovery:
        - reads stored strategy node ("current") if present
        - emits preferred_playbooks + best_cluster as reusable guidance
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data, updated_at FROM knowledge_nodes WHERE node_type='strategy' AND node_key='current' LIMIT 1"
            )
            row = cursor.fetchone()
        if not row or not row["data"]:
            return []
        try:
            blob = json.loads(str(row["data"]))
        except Exception:
            return []
        adj = blob.get("adjustments") or []
        preferred = None
        for a in adj:
            if a.get("key") == "preferred_playbooks":
                preferred = a.get("value")
        meta = blob.get("meta") or {}
        best_cluster = (meta.get("experiments") or {}).get("best_cluster")
        return [
            {
                "best_cluster": best_cluster,
                "preferred_playbooks": preferred,
                "updated_at": str(row["updated_at"]),
            }
        ]

    def _experiment_history_patterns(self, *, limit: int = 60) -> Dict[str, Any]:
        """
        Pattern discovery across experiment histories:
        - computes success_score trend
        - detects repeated failure bursts
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, status, validation_score, roi, created_at
                FROM economic_experiments
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return {"trend": "none", "recent_fail_streak": 0, "avg_validation_recent": 0.0}

        # Recent vs older avg validation
        mid = max(1, len(rows) // 2)
        recent = rows[:mid]
        older = rows[mid:]
        r_avg = sum(float(r.get("validation_score") or 0) for r in recent) / max(1, len(recent))
        o_avg = sum(float(r.get("validation_score") or 0) for r in older) / max(1, len(older)) if older else r_avg
        if r_avg > o_avg + 5:
            trend = "up"
        elif r_avg < o_avg - 5:
            trend = "down"
        else:
            trend = "flat"

        # Fail streak at head
        streak = 0
        for r in rows:
            if str(r.get("status") or "").upper() in ("FAILED", "ARCHIVED", "TERMINATED"):
                streak += 1
            else:
                break

        return {
            "trend": trend,
            "recent_fail_streak": streak,
            "avg_validation_recent": round(r_avg, 2),
            "avg_validation_older": round(o_avg, 2),
        }

