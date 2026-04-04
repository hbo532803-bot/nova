from __future__ import annotations

import logging
from typing import Any

from backend.database import get_db
from backend.db_retry import run_db_write_with_retry
from backend.knowledge.graph_store import KnowledgeGraphStore


class TrafficEngine:
    """
    Lightweight traffic + revenue simulator.
    """

    def __init__(self):
        self.kg = KnowledgeGraphStore()

    def simulate(
        self,
        *,
        mission_id: str,
        source: str,
        impressions: int = 1000,
        ctr: float = 0.03,
        conversion_rate: float = 0.12,
        lead_value: float = 200.0,
        experiment_id: int | None = None,
        scale_threshold: int = 20,
    ) -> dict[str, Any]:
        impressions = max(0, int(impressions))
        ctr = max(0.0, min(float(ctr), 1.0))
        conversion_rate = max(0.0, min(float(conversion_rate), 1.0))
        clicks = int(impressions * ctr)
        leads = int(clicks * conversion_rate)
        estimated_revenue = round(leads * float(lead_value), 2)

        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO traffic_metrics
                (mission_id, source, impressions, clicks, leads, conversion_rate, lead_value, estimated_revenue, experiment_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    source,
                    impressions,
                    clicks,
                    leads,
                    conversion_rate,
                    float(lead_value),
                    estimated_revenue,
                    experiment_id,
                ),
            )

            if experiment_id:
                status = "SCALING" if leads >= int(scale_threshold) else "FAILED"
                cursor.execute("UPDATE economic_experiments SET status=? WHERE id=?", (status, int(experiment_id)))
            conn.commit()
            return None

        run_db_write_with_retry("traffic_metrics.insert", _write)

        result = {
            "mission_id": mission_id,
            "source": source,
            "impressions": impressions,
            "clicks": clicks,
            "leads": leads,
            "conversion_rate": conversion_rate,
            "lead_value": float(lead_value),
            "estimated_revenue": estimated_revenue,
            "experiment_feedback": "scale" if leads >= int(scale_threshold) else "fail",
        }

        try:
            self.kg.upsert_node("traffic_result", mission_id, result)
            self.kg.add_edge("mission", mission_id, "GENERATED", "traffic_result", mission_id)
        except Exception:
            logging.getLogger(__name__).exception("TrafficEngine knowledge graph write failed")

        return result

    def dashboard_metrics(self, *, mission_id: str | None = None) -> dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            if mission_id:
                cursor.execute("SELECT COUNT(*) AS n FROM leads WHERE mission_id=?", (mission_id,))
                total_leads = int(cursor.fetchone()["n"])
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(impressions),0) AS impressions,
                           COALESCE(SUM(clicks),0) AS clicks,
                           COALESCE(SUM(leads),0) AS simulated_leads,
                           COALESCE(SUM(estimated_revenue),0) AS estimated_revenue
                    FROM traffic_metrics
                    WHERE mission_id=?
                    """,
                    (mission_id,),
                )
                row = cursor.fetchone()
                cursor.execute(
                    "SELECT COALESCE(SUM(amount),0) AS real_revenue FROM revenue_events WHERE mission_id=? AND status='PAID'",
                    (mission_id,),
                )
                revenue_row = cursor.fetchone()
            else:
                cursor.execute("SELECT COUNT(*) AS n FROM leads")
                total_leads = int(cursor.fetchone()["n"])
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(impressions),0) AS impressions,
                           COALESCE(SUM(clicks),0) AS clicks,
                           COALESCE(SUM(leads),0) AS simulated_leads,
                           COALESCE(SUM(estimated_revenue),0) AS estimated_revenue
                    FROM traffic_metrics
                    """
                )
                row = cursor.fetchone()
                cursor.execute(
                    "SELECT COALESCE(SUM(amount),0) AS real_revenue FROM revenue_events WHERE status='PAID'"
                )
                revenue_row = cursor.fetchone()

        impressions = int(row["impressions"] or 0)
        clicks = int(row["clicks"] or 0)
        estimated_revenue = float(row["estimated_revenue"] or 0.0)
        real_revenue = float((revenue_row["real_revenue"] if revenue_row else 0.0) or 0.0)
        simulated_leads = int(row["simulated_leads"] or 0)
        conversion_rate = round((total_leads / max(1, clicks)) * 100.0, 2)
        engagement_rate = round((clicks / max(1, impressions)) * 100.0, 2)
        return {
            "mission_id": mission_id,
            "leads_count": total_leads,
            "simulated_leads": simulated_leads,
            "impressions": impressions,
            "clicks": clicks,
            "engagement_rate_percent": engagement_rate,
            "conversion_rate_percent": conversion_rate,
            "estimated_revenue": round(estimated_revenue, 2),
            "real_revenue": round(real_revenue, 2),
        }

    def record_visit(self, *, mission_id: str, source: str = "landing", referral: str = "") -> None:
        def _write(conn):
            cursor = conn.cursor()
            src = source if not referral else f"{source}:{referral}"
            cursor.execute(
                """
                INSERT INTO traffic_metrics
                (mission_id, source, impressions, clicks, leads, conversion_rate, lead_value, estimated_revenue)
                VALUES (?, ?, 1, 1, 0, 0, 0, 0)
                """,
                (mission_id, src),
            )
            conn.commit()
            return None

        run_db_write_with_retry("traffic_metrics.record_visit", _write)
