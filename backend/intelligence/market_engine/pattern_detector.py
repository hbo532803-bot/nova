import datetime
import math
from backend.database import get_db


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

            # -----------------------------------------
            # Fetch all niches for current week
            # -----------------------------------------
            cursor.execute("""
                SELECT id, niche_name,
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
                print("⚠ No niches found for this week")
                return []

            total_niches = len(rows)

            # -----------------------------------------
            # Top 20% relative ranking rule
            # -----------------------------------------
            top_count = max(1, math.ceil(total_niches * 0.20))

            for index, row in enumerate(rows):

                niche_id, niche, long_t, medium_t, short_t, cash = row

                # Optional sanity trend filter (very low trend ignore)
                trend_filter = (
                    (long_t or 0) >= 5 and
                    (medium_t or 0) >= 5
                )

                if index < top_count and trend_filter:
                    status = "OPPORTUNITY"
                    opportunity_list.append(niche)
                else:
                    status = "MONITOR"

                cursor.execute("""
                    UPDATE market_niches
                    SET status = ?
                    WHERE id = ?
                """, (status, niche_id))

            conn.commit()

        print("✅ Pattern detection completed")
        print("🎯 Opportunity Niches:", opportunity_list)

        return opportunity_list