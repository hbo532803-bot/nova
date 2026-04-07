from __future__ import annotations

from typing import Any

from backend.database import get_db


class MetricsEngine:
    """
    Aggregates real capability metrics from tracked signals.
    All outputs include real vs simulated segregation.
    """

    def compute(
        self,
        *,
        mission_id: str | None = None,
        experiment_id: int | None = None,
    ) -> dict[str, Any]:
        where = []
        params: list[Any] = []
        if mission_id:
            where.append("mission_id=?")
            params.append(mission_id)
        if experiment_id is not None:
            where.append("experiment_id=?")
            params.append(int(experiment_id))
        where_sql = "WHERE " + " AND ".join(where) if where else ""

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    SUM(CASE WHEN event_type='page_view' AND is_simulated=0 THEN 1 ELSE 0 END) AS real_page_views,
                    SUM(CASE WHEN event_type='click' AND is_simulated=0 THEN 1 ELSE 0 END) AS real_clicks,
                    SUM(CASE WHEN event_type='lead' AND is_simulated=0 THEN 1 ELSE 0 END) AS real_leads,
                    SUM(CASE WHEN event_type='payment' AND is_simulated=0 THEN 1 ELSE 0 END) AS real_payments,
                    SUM(CASE WHEN event_type='page_view' AND is_simulated=1 THEN COALESCE(event_value, 1) ELSE 0 END) AS simulated_page_views,
                    SUM(CASE WHEN event_type='click' AND is_simulated=1 THEN COALESCE(event_value, 1) ELSE 0 END) AS simulated_clicks,
                    SUM(CASE WHEN event_type='lead' AND is_simulated=1 THEN COALESCE(event_value, 1) ELSE 0 END) AS simulated_leads,
                    SUM(CASE WHEN event_type='payment' AND is_simulated=1 THEN COALESCE(event_value, 1) ELSE 0 END) AS simulated_payments,
                    COUNT(DISTINCT CASE WHEN is_simulated=0 THEN COALESCE(session_id, 'anon:' || id) END) AS real_unique_users
                FROM real_signal_events
                {where_sql}
                """,
                tuple(params),
            )
            row = cursor.fetchone()

            cursor.execute(
                f"""
                SELECT COALESCE(SUM(amount),0) AS paid_revenue
                FROM revenue_events
                {'WHERE mission_id=?' if mission_id else ''}
                """,
                ((mission_id,) if mission_id else ()),
            )
            revenue_row = cursor.fetchone()

        real_page_views = int((row["real_page_views"] or 0) if row else 0)
        real_clicks = int((row["real_clicks"] or 0) if row else 0)
        real_leads = int((row["real_leads"] or 0) if row else 0)
        real_unique_users = int((row["real_unique_users"] or 0) if row else 0)
        paid_revenue = float((revenue_row["paid_revenue"] or 0.0) if revenue_row else 0.0)

        ctr = (real_clicks / real_page_views) if real_page_views else 0.0
        conversion_rate = (real_leads / real_clicks) if real_clicks else 0.0
        rpu = (paid_revenue / real_unique_users) if real_unique_users else 0.0

        return {
            "mission_id": mission_id,
            "experiment_id": experiment_id,
            "real": {
                "page_views": real_page_views,
                "clicks": real_clicks,
                "leads": real_leads,
                "payments": int((row["real_payments"] or 0) if row else 0),
                "unique_users": real_unique_users,
            },
            "simulated": {
                "page_views": int(float((row["simulated_page_views"] or 0) if row else 0)),
                "clicks": int(float((row["simulated_clicks"] or 0) if row else 0)),
                "leads": int(float((row["simulated_leads"] or 0) if row else 0)),
                "payments": int(float((row["simulated_payments"] or 0) if row else 0)),
            },
            "metrics": {
                "click_through_rate": round(ctr, 4),
                "conversion_rate": round(conversion_rate, 4),
                "revenue_per_user": round(rpu, 2),
                "paid_revenue": round(paid_revenue, 2),
            },
        }
