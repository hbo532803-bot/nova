from backend.database import get_db
from datetime import datetime


class ConfidenceEngine:

    MIN_SCORE = 0
    MAX_SCORE = 100
    DEFAULT_SCORE = 50

    def _map_autonomy(self, score):

        if score < 60:
            return "MANUAL_ONLY"
        elif score < 75:
            return "SEMI_AUTO_LOW_RISK"
        elif score < 85:
            return "SEMI_AUTO_EXPANDED"
        else:
            return "FULL_AUTONOMY"

    def _ensure_row(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM confidence_state WHERE id=1"
            )

            if not cursor.fetchone():

                cursor.execute(
                    """
                    INSERT INTO confidence_state (id,score,autonomy)
                    VALUES (1,?,?)
                    """,
                    (self.DEFAULT_SCORE, "MANUAL_ONLY"),
                )

                conn.commit()

    def get_state(self):

        self._ensure_row()

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT score, autonomy FROM confidence_state WHERE id=1"
            )

            row = cursor.fetchone()

            return {
                "score": row["score"],
                "autonomy": row["autonomy"]
            }

    def adjust(self, delta):

        state = self.get_state()

        new_score = max(
            self.MIN_SCORE,
            min(self.MAX_SCORE, state["score"] + delta)
        )

        autonomy = self._map_autonomy(new_score)

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE confidence_state
                SET score=?, autonomy=?, updated_at=?
                WHERE id=1
                """,
                (new_score, autonomy, datetime.utcnow())
            )

            conn.commit()

        return {
            "score": new_score,
            "autonomy": autonomy
        }

    def success(self):
        return self.adjust(+1)

    def failure(self):
        return self.adjust(-1)

    def set_score(self, value):

        value = max(self.MIN_SCORE, min(self.MAX_SCORE, value))

        autonomy = self._map_autonomy(value)

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE confidence_state
                SET score=?, autonomy=?, updated_at=?
                WHERE id=1
                """,
                (value, autonomy, datetime.utcnow())
            )

            conn.commit()

        return {
            "score": value,
            "autonomy": autonomy
        }

    def get_score(self):
        return self.get_state()["score"]

    def get_autonomy(self):
        return self.get_state()["autonomy"]