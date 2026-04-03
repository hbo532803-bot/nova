from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from backend.database import get_db
from backend.frontend_api.event_bus import broadcast
from backend.intelligence.experiment_analytics import ExperimentAnalytics
from backend.system.stability import SystemStability
from backend.knowledge.reasoner import KnowledgeGraphReasoner
from backend.intelligence.mission_planner import MissionPlanner


class CognitiveCycle:
    """
    Cognitive architecture: observe → reason → plan → act → learn.
    This layer must NOT bypass NovaCore/Supervisor/ExecutionEngine; it only emits commands/plans.
    """

    SETTINGS_KEY = "cognitive_last"

    def __init__(self):
        self.analytics = ExperimentAnalytics()
        self.stability = SystemStability()
        self.kg_reasoner = KnowledgeGraphReasoner()
        self.planner = MissionPlanner()

    def run(self, *, goal_hint: str = "autonomous_mission") -> Dict[str, Any]:
        observed = self.observe()
        reasoning = self.reason(observed)
        plan = self.plan(goal_hint, observed, reasoning)
        payload = {"observe": observed, "reason": reasoning, "plan": plan, "updated_at": datetime.utcnow().isoformat()}
        self._persist(payload)
        return {"ok": True, **payload}

    def observe(self) -> Dict[str, Any]:
        return {
            "stability": self.stability.health(),
            "portfolio": self.analytics.summary(limit=50),
            "kg": self.kg_reasoner.insights(limit_edges=1000),
        }

    def reason(self, observed: Dict[str, Any]) -> Dict[str, Any]:
        kg = observed.get("kg") or {}
        portfolio = observed.get("portfolio") or {}
        trend = str(portfolio.get("trend") or "flat")

        outcome_counts = kg.get("outcome_counts") or {}
        failure = float(outcome_counts.get("failure") or 0)
        success = float(outcome_counts.get("success") or 0)
        win_rate = (success / max(1.0, success + failure)) if (success + failure) else 0.0

        return {
            "portfolio_trend": trend,
            "kg_win_rate": round(win_rate, 3),
            "reusable": kg.get("reusable_strategies") or [],
            "recommendation": "explore" if trend == "down" else "exploit",
        }

    def plan(self, goal_hint: str, observed: Dict[str, Any], reasoning: Dict[str, Any]) -> Dict[str, Any]:
        mission_id = datetime.utcnow().isoformat()
        task_graph = self.planner.build_task_graph(goal_hint, mission_id=mission_id)
        return {"mission_id": mission_id, "goal": goal_hint, "task_graph": task_graph}

    def last(self) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_settings WHERE key=?", (self.SETTINGS_KEY,))
            row = cursor.fetchone()
        if not row or not row["value"]:
            return None
        try:
            return json.loads(str(row["value"]))
        except Exception:
            return {"raw": str(row["value"])}

    def _persist(self, payload: Dict[str, Any]) -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, ?)",
                (self.SETTINGS_KEY, json.dumps(payload), datetime.utcnow()),
            )
            conn.commit()
        try:
            broadcast({"type": "log", "level": "info", "message": "CognitiveCycle updated"})
        except Exception:
            pass

