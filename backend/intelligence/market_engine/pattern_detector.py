import datetime
import math

from backend.database import get_db
from backend.frontend_api.event_bus import broadcast


class MarketPatternDetector:

    def __init__(self):

        self.week_tag = self._current_week()

    def _current_week(self):

        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    def detect_patterns(self):

        opportunity_list = []

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT id,
                       niche_name,
                       long_term_trend,
                       medium_term_trend,
                       short_term_spike,
                       cash_score
                FROM market_niches
                WHERE week_tag = ?
                ORDER BY cash_score DESC
            """, (self.week_tag,))

            rows = cursor.fetchall()

            if not rows:

                broadcast({
                    "type": "log",
                    "level": "warn",
                    "message": "No niches found for this week"
                })

                return []

            total_niches = len(rows)

            top_count = max(1, math.ceil(total_niches * 0.20))

            updates = []

            for index, row in enumerate(rows):

                niche_id = row["id"]

                niche = row["niche_name"]

                long_t = row["long_term_trend"] or 0
                medium_t = row["medium_term_trend"] or 0
                spike = row["short_term_spike"] or 0
                cash = row["cash_score"] or 0

                trend_filter = long_t >= 5 and medium_t >= 5

                spike_filter = spike >= 10

                cash_filter = cash >= 40

                if index < top_count and trend_filter and (spike_filter or cash_filter):

                    status = "OPPORTUNITY"

                    opportunity_list.append(niche)

                else:

                    status = "MONITOR"

                updates.append((status, niche_id, self.week_tag))

            cursor.executemany(
                """
                UPDATE market_niches
                SET status = ?
                WHERE id = ?
                AND week_tag = ?
                """,
                updates
            )

            conn.commit()

        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Pattern detection complete ({len(opportunity_list)} opportunities)"
        })

        return opportunity_list