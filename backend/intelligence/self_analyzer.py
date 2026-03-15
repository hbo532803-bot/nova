from backend.database import get_db


class SelfAnalyzer:

    """
    Nova Self Analyzer
    """

    def generate_system_report(self):

        return {
            "confidence_level": self._get_confidence(),
            "experiment_stats": self._get_experiment_stats(),
            "agent_stats": self._get_agent_stats(),
            "reflection_count": self._get_reflection_count()
        }

    # -------------------------------
    # CONFIDENCE
    # -------------------------------

    def _get_confidence(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT score, autonomy FROM confidence_state ORDER BY id DESC LIMIT 1"
            )

            row = cursor.fetchone()

            if not row:
                return {"score": 0, "autonomy": "UNKNOWN"}

            return {
                "score": row["score"],
                "autonomy": row["autonomy"]
            }

    # -------------------------------
    # EXPERIMENT STATS
    # -------------------------------

    def _get_experiment_stats(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS c FROM economic_experiments")
            total = cursor.fetchone()["c"]

            cursor.execute(
                "SELECT COUNT(*) AS c FROM economic_experiments WHERE status='FAILED'"
            )
            failed = cursor.fetchone()["c"]

            cursor.execute(
                "SELECT COUNT(*) AS c FROM economic_experiments WHERE status='SCALING'"
            )
            scaling = cursor.fetchone()["c"]

            return {
                "total_experiments": total,
                "failed_experiments": failed,
                "scaling_experiments": scaling
            }

    # -------------------------------
    # AGENTS
    # -------------------------------

    def _get_agent_stats(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS c FROM agents")

            total = cursor.fetchone()["c"]

            return {"total_agents": total}

    # -------------------------------
    # REFLECTION COUNT
    # -------------------------------

    def _get_reflection_count(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS c FROM reflections")

            return cursor.fetchone()["c"]