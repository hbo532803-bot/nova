import datetime
from collections import defaultdict

from backend.database import get_db


class MarketScoringEngine:

    def __init__(self):

        self.week_tag = self._current_week()

    # --------------------------------------
    # WEEK TAG
    # --------------------------------------

    def _current_week(self):

        today = datetime.date.today()

        return f"{today.year}-W{today.isocalendar()[1]}"

    # --------------------------------------
    # CLEAR WEEK DATA
    # --------------------------------------

    def clear_week(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM market_niches
                WHERE week_tag = ?
            """, (self.week_tag,))

            conn.commit()

    # --------------------------------------
    # FETCH SIGNALS
    # --------------------------------------

    def fetch_signals(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT niche_name, signal_type, value
                FROM market_signals
                WHERE week_tag = ?
            """, (self.week_tag,))

            rows = cursor.fetchall()

        data = defaultdict(dict)

        for niche, signal_type, value in rows:

            data[niche][signal_type] = value

        return data

    # --------------------------------------
    # NORMALIZE
    # --------------------------------------

    def normalize(self, value, max_value):

        if max_value == 0:
            return 0

        score = (value / max_value) * 100

        return min(100, max(0, score))

    # --------------------------------------
    # COMPUTE SCORES
    # --------------------------------------

    def compute_scores(self):

        signals = self.fetch_signals()

        if not signals:

            print("⚠ No signals found")

            return

        max_job_posts = max([v.get("job_posts", 1) for v in signals.values()])
        max_budget = max([v.get("avg_budget", 1) for v in signals.values()])
        max_reddit = max([v.get("mentions", 1) for v in signals.values()])
        max_gigs = max([v.get("gig_count", 1) for v in signals.values()])

        with get_db() as conn:

            cursor = conn.cursor()

            for niche, values in signals.items():

                job_posts = values.get("job_posts", 0)
                avg_budget = values.get("avg_budget", 0)

                trend_growth = values.get("trend_growth", 0)
                spike_score = values.get("spike_score", 0)

                urgent_flag = values.get("urgent_flag", 0)

                reddit_mentions = values.get("mentions", 0)
                gig_count = values.get("gig_count", 0)

                google_competition = values.get("competition_score", 0)

                demand_score = (
                    self.normalize(job_posts, max_job_posts) * 0.5 +
                    trend_growth * 0.3 +
                    self.normalize(reddit_mentions, max_reddit) * 0.2 +
                    urgent_flag * 5
                )

                money_score = self.normalize(avg_budget, max_budget)

                urgency_score = spike_score

                competition_score = (
                    self.normalize(gig_count, max_gigs) * 0.5 +
                    self.normalize(google_competition, max_job_posts) * 0.5
                )

                cash_score = (
                    demand_score * 0.35 +
                    money_score * 0.30 +
                    urgency_score * 0.20 +
                    (100 - competition_score) * 0.15
                )

                cash_score = round(min(100, max(0, cash_score)), 2)

                cursor.execute("""
                    INSERT INTO market_niches (
                        niche_name,
                        week_tag,
                        demand_score,
                        competition_score,
                        money_score,
                        urgency_score,
                        cash_score,
                        long_term_trend,
                        medium_term_trend,
                        short_term_spike
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    niche,
                    self.week_tag,
                    round(demand_score, 2),
                    round(competition_score, 2),
                    round(money_score, 2),
                    round(urgency_score, 2),
                    cash_score,
                    trend_growth,
                    trend_growth,
                    spike_score
                ))

            conn.commit()

        print("✅ Stable scoring completed")