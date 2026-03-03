from datetime import datetime
from backend.database import get_db

DAILY_CALL_LIMIT = 100
DAILY_TOKEN_LIMIT = 50000


def _today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def record_call(tokens: int = 0):
    today = _today()

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT calls, tokens FROM api_usage WHERE date = ?",
            (today,)
        )
        row = cursor.fetchone()

        if row:
            calls, tok = row
            cursor.execute(
                "UPDATE api_usage SET calls=?, tokens=? WHERE date=?",
                (calls + 1, tok + tokens, today)
            )
        else:
            cursor.execute(
                "INSERT INTO api_usage (date, calls, tokens) VALUES (?, ?, ?)",
                (today, 1, tokens)
            )

        conn.commit()


def check_budget():
    today = _today()

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT calls, tokens FROM api_usage WHERE date = ?",
            (today,)
        )
        row = cursor.fetchone()

        if not row:
            return True

        calls, tokens = row

        if calls >= DAILY_CALL_LIMIT:
            return False

        if tokens >= DAILY_TOKEN_LIMIT:
            return False

        return True
