import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "nova.db"


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False  # ✅ allow multi-thread access
    )
    conn.row_factory = sqlite3.Row

    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")

    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode = WAL;")

    return conn


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # ---------------- GOALS ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            plan_json TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------- PLAN MEMORY ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            plan_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------- REFLECTIONS ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reflections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT,
            outcome TEXT,
            embedding TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------- CONFIDENCE STATE ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS confidence_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            autonomy TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ---------------- SYSTEM SETTINGS ----------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS economic_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            allocated_budget REAL,
            status TEXT,
            revenue REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            total_revenue REAL DEFAULT 0,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            calls INTEGER DEFAULT 0,
            tokens INTEGER DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_name TEXT,
            cash_score REAL,
            proposed_budget REAL,
            status TEXT,
           created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()


# Backward compatibility
def get_db():
    return get_connection()