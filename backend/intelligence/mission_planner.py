from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from backend.database import get_db
from backend.execution.action_types import ActionType


class MissionPlanner:
    """
    Translates a goal into a multi-step mission task graph compatible with TaskGraphEngine.
    Produces:
    - dependency relationships
    - parallelizable nodes
    - intermediate outputs via mission memory handled by Supervisor
    """

    def build_task_graph(self, goal: str, *, mission_id: str) -> Dict[str, Any]:
        preferred = self._preferred_playbooks()

        nodes: List[Dict[str, Any]] = []

        # Observe/research node
        nodes.append(
            {
                "id": "research",
                "name": "Research opportunities",
                "required_capabilities": ["research", "opportunity_discovery"],
                "depends_on": [],
                "actions": [
                    {
                        "type": ActionType.RESEARCH_RUN.value,
                        "payload": {"max_proposals": 5},
                        "assumed_failure": "research_engine_fails",
                        "failure_impact": "no_new_opportunities",
                    }
                ],
            }
        )

        # Portfolio assessment can run in parallel with research
        nodes.append(
            {
                "id": "portfolio_eval",
                "name": "Evaluate experiment portfolio",
                "required_capabilities": ["finance", "portfolio", "analysis"],
                "depends_on": [],
                "actions": [
                    {
                        "type": ActionType.EXPERIMENT_EVALUATE_PORTFOLIO.value,
                        "payload": {"limit": 50},
                        "assumed_failure": "portfolio_evaluate_fails",
                        "failure_impact": "no_lifecycle_signal",
                    }
                ],
            }
        )

        # Strategy learning depends on having signals available
        nodes.append(
            {
                "id": "learn",
                "name": "Learn strategy",
                "required_capabilities": ["analysis", "finance"],
                "depends_on": ["research", "portfolio_eval"],
                "actions": [
                    {
                        "type": ActionType.STRATEGY_LEARN.value,
                        "payload": {"lookback": 120},
                        "assumed_failure": "strategy_learning_fails",
                        "failure_impact": "no_strategy_adjustment",
                    }
                ],
            }
        )

        # Optional: recommend playbooks in shared_context (no mutation), represented as reflection action
        nodes.append(
            {
                "id": "plan_next",
                "name": "Plan next experiments",
                "required_capabilities": ["growth_experimentation", "product_research"],
                "depends_on": ["learn"],
                "actions": [
                    {
                        "type": ActionType.REFLECTION_RECORD.value,
                        "payload": {
                            "reflection": {
                                "cycle_id": mission_id,
                                "primary_goal_snapshot": goal,
                                "input_objective": goal,
                                "execution_result": f"preferred_playbooks={preferred}",
                                "success": True,
                                "confidence_before": 0,
                                "confidence_after": 0,
                            }
                        },
                        "assumed_failure": "reflection_write_fails",
                        "failure_impact": "planning_signal_lost",
                    }
                ],
            }
        )

        return {"mission_id": mission_id, "goal": goal, "nodes": nodes}

    def _preferred_playbooks(self) -> List[str]:
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key='strategy_adjustments'")
                row = cursor.fetchone()
            if not row or not row["value"]:
                return []
            blob = json.loads(str(row["value"]))
            for a in blob.get("adjustments") or []:
                if a.get("key") == "preferred_playbooks":
                    v = a.get("value")
                    return list(v) if isinstance(v, list) else []
        except Exception:
            return []
        return []

