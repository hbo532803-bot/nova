from backend.database import get_connection


def get_setting(key: str, default=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return row["value"]
    return default


def set_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO system_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
    """, (key, value))

    conn.commit()
    conn.close()
