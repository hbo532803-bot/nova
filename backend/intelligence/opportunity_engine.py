from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from backend.database import get_db
from backend.frontend_api.event_bus import broadcast

from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner
from backend.intelligence.economic_controller import EconomicController
from backend.knowledge.graph_store import KnowledgeGraphStore


class OpportunityEngine:
    """
    Opportunity Engine (docs goal):
    - signal collection
    - pattern detection
    - opportunity scoring
    - proposal generation

    Uses the existing Market Engine pipeline and stores results in existing tables:
    - market_signals, market_niches, market_proposals
    """

    def __init__(self):
        self.market = MarketWeeklyRunner()
        self.econ = EconomicController()
        self.kg = KnowledgeGraphStore()

    def run_discovery(self) -> Dict[str, Any]:
        broadcast({"type": "log", "level": "info", "message": "Opportunity discovery started"})
        opportunities = self.market.run_full_weekly_cycle()
        proposals = self.list_proposals()
        return {"opportunities": opportunities, "proposals": proposals}

    def _current_week(self) -> str:
        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    def list_proposals(self, week_tag: Optional[str] = None) -> List[Dict[str, Any]]:
        week = week_tag or self._current_week()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, niche_name, week_tag, cash_score, proposed_budget, status, created_at
                FROM market_proposals
                WHERE week_tag = ?
                ORDER BY cash_score DESC
                """,
                (week,),
            )
            rows = cursor.fetchall()
        return [dict(r) for r in rows]

    def approve_proposal(self, proposal_id: int) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE market_proposals SET status='APPROVED' WHERE id=?", (proposal_id,))
            conn.commit()
        return {"id": proposal_id, "status": "APPROVED"}

    def reject_proposal(self, proposal_id: int) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE market_proposals SET status='REJECTED' WHERE id=?", (proposal_id,))
            conn.commit()
        return {"id": proposal_id, "status": "REJECTED"}

    def convert_to_experiment(self, proposal_id: int) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                # Acquire a write transaction early to prevent partial commits under concurrent access.
                cursor.execute("BEGIN IMMEDIATE")

                cursor.execute(
                    "SELECT niche_name, proposed_budget, status FROM market_proposals WHERE id=?",
                    (proposal_id,),
                )
                row = cursor.fetchone()
                if not row:
                    conn.rollback()
                    return {"error": "proposal_not_found"}

                if row["status"] not in ("APPROVED", "PENDING"):
                    conn.rollback()
                    return {"error": "proposal_not_convertible", "status": row["status"]}

                niche = row["niche_name"]
                budget = float(row["proposed_budget"] or 0)

                result = self.econ.create_experiment_from_market(niche_name=niche, budget=budget, conn=conn)

                if result.get("status") == "approved":
                    cursor.execute("UPDATE market_proposals SET status='LAUNCHED' WHERE id=?", (proposal_id,))

                conn.commit()

            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                return {"proposal_id": proposal_id, "success": False, "error": str(e)}

        # Knowledge graph linking remains best-effort and non-blocking.
        if isinstance(result, dict) and result.get("status") == "approved":
            try:
                self.kg.upsert_node("opportunity", str(proposal_id), {"niche": niche, "budget": budget, "status": "LAUNCHED"})
                self.kg.upsert_node("experiment", str(result.get("experiment") or niche), {"name": niche})
                self.kg.add_edge("opportunity", str(proposal_id), "LAUNCHED_EXPERIMENT", "experiment", str(niche))
            except Exception:
                pass

        return {"proposal_id": proposal_id, "experiment": result}

