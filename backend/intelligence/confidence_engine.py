# backend/intelligence/confidence_engine.py

from backend.database import get_connection
from datetime import datetime


class ConfidenceEngine:

    MIN_SCORE = 0
    MAX_SCORE = 100
    DEFAULT_SCORE = 50

    # ---------------------------------
    # Ensure Table Exists
    # ---------------------------------
    def _ensure_table(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score REAL NOT NULL,
                autonomy TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ---------------------------------
    # Internal Autonomy Mapping
    # ---------------------------------
    def _map_autonomy(self, score: float) -> str:
        if score < 60:
            return "MANUAL_ONLY"
        elif score < 75:
            return "SEMI_AUTO_LOW_RISK"
        elif score < 85:
            return "SEMI_AUTO_EXPANDED"
        else:
            return "FULL_AUTONOMY"

    # ---------------------------------
    # Get Latest State
    # ---------------------------------
    def get_state(self):
        self._ensure_table()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT score, autonomy
            FROM confidence_state
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "score": row["score"],
                "autonomy": row["autonomy"]
            }

        # Initialize if empty
        return self.set_score(self.DEFAULT_SCORE)

    # ---------------------------------
    # Adjust Confidence
    # ---------------------------------
    def adjust(self, delta: float):
        state = self.get_state()
        current = state["score"]

        new_score = max(
            self.MIN_SCORE,
            min(self.MAX_SCORE, current + delta)
        )

        autonomy = self._map_autonomy(new_score)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO confidence_state (score, autonomy, updated_at)
            VALUES (?, ?, ?)
        """, (new_score, autonomy, datetime.utcnow()))

        conn.commit()
        conn.close()

        return {
            "score": new_score,
            "autonomy": autonomy
        }

    # ---------------------------------
    # Direct Set (Admin Only)
    # ---------------------------------
    def set_score(self, value: float):
        value = max(self.MIN_SCORE, min(self.MAX_SCORE, value))
        autonomy = self._map_autonomy(value)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO confidence_state (score, autonomy, updated_at)
            VALUES (?, ?, ?)
        """, (value, autonomy, datetime.utcnow()))

        conn.commit()
        conn.close()

        return {
            "score": value,
            "autonomy": autonomy
        }

    # ---------------------------------
    # Quick Helpers
    # ---------------------------------
    def get_score(self):
        return self.get_state()["score"]

    def get_autonomy(self):
        return self.get_state()["autonomy"]