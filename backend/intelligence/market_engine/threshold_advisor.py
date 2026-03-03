import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "backend/nova.db"


class ThresholdAdvisor:

    def analyze(self):

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT week_tag, attack_count, avg_cash_score
            FROM market_memory
            ORDER BY id DESC
            LIMIT 3
        """)

        rows = cursor.fetchall()
        conn.close()

        if len(rows) < 3:
            return {"status": "insufficient_data"}

        no_attack_weeks = sum(1 for r in rows if r[1] == 0)
        avg_cash = sum(r[2] for r in rows) / len(rows)

        suggestion = "no_change"
        reason = "System stable"

        if no_attack_weeks == 3:
            suggestion = "decrease_threshold"
            reason = "No attack zones detected for 3 consecutive weeks"

        elif avg_cash > 75:
            suggestion = "increase_threshold"
            reason = "Market too hot, tightening filter"

        return {
            "suggestion": suggestion,
            "reason": reason,
            "avg_cash_last_3_weeks": round(avg_cash, 2)
        }