import sqlite3
from pathlib import Path
from contextlib import contextmanager

# ---------------------------------
# Database Path (ONLY defined here)
# ---------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nova.db"


# ---------------------------------
# Connection Factory
# ---------------------------------
def _create_connection():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    # SQLite stability settings
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=30000;")

    return conn


# ---------------------------------
# Public DB Access (ONLY method)
# ---------------------------------
@contextmanager
def get_db():

    conn = _create_connection()

    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------
# Health Check (optional utility)
# ---------------------------------
def db_health_check():

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True

    except Exception as e:
        print("DB health check failed:", e)
        return False