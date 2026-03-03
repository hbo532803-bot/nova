from backend.database import get_connection
from backend.intelligence.system_settings import get_setting


class SystemSelfAnalyzer:

    def generate_system_report(self):

        return {
            "goals_stats": self._get_goal_stats(),
            "confidence_level": self._get_confidence(),
            "system_configuration": {
                "semantic_threshold": get_setting("semantic_threshold", "0.75"),
                "reasoning_depth": get_setting("reasoning_depth", "1"),
                "recursive_planning": get_setting("recursive_planning", "disabled")
            }
        }

    def _get_goal_stats(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM goals")
        total = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(DISTINCT goal) as unique_goals FROM goals")
        unique_goals = cursor.fetchone()["unique_goals"]

        conn.close()

        return {
            "total_goals": total,
            "unique_goals": unique_goals
        }

    def _get_confidence(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT score, autonomy FROM confidence_state ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()

        conn.close()

        if row:
            return {
                "score": row["score"],
                "autonomy": row["autonomy"]
            }

        return {
            "score": 50,
            "autonomy": "LIMITED"
        }
SelfAnalyzer = SystemSelfAnalyzer
