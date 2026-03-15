from backend.database import get_db


class ThresholdAdvisor:

    def analyze(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT week_tag, attack_count, avg_cash_score
                FROM market_memory
                ORDER BY id DESC
                LIMIT 3
            """)

            rows = cursor.fetchall()

        if len(rows) < 3:

            return {
                "status": "insufficient_data"
            }

        no_attack_weeks = sum(
            1 for r in rows if r["attack_count"] == 0
        )

        avg_cash = sum(
            r["avg_cash_score"] for r in rows
        ) / len(rows)

        suggestion = "no_change"

        reason = "System stable"

        if no_attack_weeks >= 3:

            suggestion = "decrease_threshold"

            reason = "No opportunities detected for 3 weeks"

        elif avg_cash > 75:

            suggestion = "increase_threshold"

            reason = "Market overheated"

        elif avg_cash < 35:

            suggestion = "decrease_threshold"

            reason = "Market too cold"

        return {
            "suggestion": suggestion,
            "reason": reason,
            "avg_cash_last_3_weeks": round(avg_cash, 2)
        }