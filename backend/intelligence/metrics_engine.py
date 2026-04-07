from __future__ import annotations

from typing import Any

from backend.database import get_db


class MetricsEngine:
    """
    Aggregates reliable metrics with strict real-vs-simulated separation.
    """

    DEFAULT_MIN_SAMPLE_THRESHOLD = 50

    def compute(
        self,
        *,
        mission_id: str | None = None,
        experiment_id: int | None = None,
        min_sample_threshold: int | None = None,
    ) -> dict[str, Any]:
        threshold = int(min_sample_threshold or self.DEFAULT_MIN_SAMPLE_THRESHOLD)
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

            cursor.execute(
                f"""
                SELECT
                    COALESCE(SUM(CASE WHEN event_type='lead' AND lead_quality='high' THEN 1 ELSE 0 END),0) AS high_quality,
                    COALESCE(SUM(CASE WHEN event_type='lead' AND lead_quality='medium' THEN 1 ELSE 0 END),0) AS medium_quality,
                    COALESCE(SUM(CASE WHEN event_type='lead' AND lead_quality='low' THEN 1 ELSE 0 END),0) AS low_quality
                FROM session_journey
                {where_sql}
                """,
                tuple(params),
            )
            quality_row = cursor.fetchone()

            cursor.execute(
                f"""
                SELECT traffic_source, COUNT(*) AS n
                FROM session_journey
                {where_sql}
                GROUP BY traffic_source
                """,
                tuple(params),
            )
            traffic_rows = cursor.fetchall()

        real_page_views = int((row["real_page_views"] or 0) if row else 0)
        real_clicks = int((row["real_clicks"] or 0) if row else 0)
        real_leads = int((row["real_leads"] or 0) if row else 0)
        real_payments = int((row["real_payments"] or 0) if row else 0)
        real_unique_users = int((row["real_unique_users"] or 0) if row else 0)
        paid_revenue = float((revenue_row["paid_revenue"] or 0.0) if revenue_row else 0.0)

        view_to_click = (real_clicks / real_page_views) if real_page_views else 0.0
        click_to_lead = (real_leads / real_clicks) if real_clicks else 0.0
        lead_to_payment = (real_payments / real_leads) if real_leads else 0.0
        rpu = (paid_revenue / real_unique_users) if real_unique_users else 0.0

        total_events_real = real_page_views + real_clicks + real_leads + real_payments
        is_reliable = real_page_views >= threshold
        reliability = {
            "total_views": real_page_views,
            "total_events": total_events_real,
            "min_sample_threshold": threshold,
            "is_data_reliable": is_reliable,
            "quality_flag": "reliable" if is_reliable else "low_sample",
        }

        return {
            "mission_id": mission_id,
            "experiment_id": experiment_id,
            "real": {
                "page_views": real_page_views,
                "clicks": real_clicks,
                "leads": real_leads,
                "payments": real_payments,
                "unique_users": real_unique_users,
            },
            "simulated": {
                "page_views": int(float((row["simulated_page_views"] or 0) if row else 0)),
                "clicks": int(float((row["simulated_clicks"] or 0) if row else 0)),
                "leads": int(float((row["simulated_leads"] or 0) if row else 0)),
                "payments": int(float((row["simulated_payments"] or 0) if row else 0)),
            },
            "metrics": {
                "click_through_rate": round(view_to_click, 4),
                "conversion_rate": round(click_to_lead, 4),
                "revenue_per_user": round(rpu, 2),
                "paid_revenue": round(paid_revenue, 2),
            },
            "funnel": {
                "view_to_click_rate": round(view_to_click, 4),
                "click_to_lead_rate": round(click_to_lead, 4),
                "lead_to_payment_rate": round(lead_to_payment, 4),
                "dropoff": {
                    "views_without_click": max(0, real_page_views - real_clicks),
                    "clicks_without_lead": max(0, real_clicks - real_leads),
                    "leads_without_payment": max(0, real_leads - real_payments),
                },
            },
            "lead_quality": {
                "high": int((quality_row["high_quality"] or 0) if quality_row else 0),
                "medium": int((quality_row["medium_quality"] or 0) if quality_row else 0),
                "low": int((quality_row["low_quality"] or 0) if quality_row else 0),
            },
            "traffic_source": {str(r["traffic_source"] or "unknown"): int(r["n"] or 0) for r in traffic_rows},
            "reliability": reliability,
        }
