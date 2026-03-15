from backend.database import get_db


def get_setting(key: str, default=None):

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute(
            "SELECT value FROM system_settings WHERE key = ?",
            (key,)
        )

        row = cursor.fetchone()

    if row:
        return row["value"]

    return default


def set_setting(key: str, value: str):

    with get_db() as conn:

        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO system_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
        """, (key, value))

        conn.commit()