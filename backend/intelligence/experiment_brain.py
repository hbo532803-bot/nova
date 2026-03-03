import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "nova.db"


class ExperimentBrain:

    def __init__(self):
        pass

    def analyze_experiments(self):

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, revenue, cost, status
            FROM economic_experiments
            WHERE status = 'ACTIVE'
        """)

        rows = cursor.fetchall()

        suggestions = {
            "kill": [],
            "scale": [],
            "monitor": []
        }

        for row in rows:
            exp_id, name, revenue, cost, status = row

            revenue = revenue or 0
            cost = cost or 0

            # Avoid division by zero
            roi = revenue / cost if cost > 0 else 0

            # Count cycles (approx using reflection count or log count later)
            cursor.execute("""
                SELECT COUNT(*)
                FROM execution_logs
                WHERE experiment_id = ?
            """, (exp_id,))
            cycle_count = cursor.fetchone()[0]

            # ---- RULES ----

            if cycle_count >= 3 and roi < 0.8:
                suggestions["kill"].append({
                    "id": exp_id,
                    "name": name,
                    "roi": round(roi, 2),
                    "cycles": cycle_count
                })

            elif cycle_count >= 2 and roi > 1.5:
                suggestions["scale"].append({
                    "id": exp_id,
                    "name": name,
                    "roi": round(roi, 2),
                    "cycles": cycle_count
                })

            else:
                suggestions["monitor"].append({
                    "id": exp_id,
                    "name": name,
                    "roi": round(roi, 2),
                    "cycles": cycle_count
                })

        conn.close()

        print("🧠 Experiment analysis complete")
        return suggestions