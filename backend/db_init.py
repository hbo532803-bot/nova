from pathlib import Path
import sqlite3

# 🔥 SINGLE SOURCE OF TRUTH
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "nova.db"

def get_connection():
    print(f"📂 Using DB at: {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def initialize_all_tables(reset=False):
    conn = get_connection()
    cursor = conn.cursor()

    if reset:
        print("⚠ RESET MODE: Dropping all tables")
        cursor.executescript("""
        DROP TABLE IF EXISTS goals;
        DROP TABLE IF EXISTS plan_memory;
        DROP TABLE IF EXISTS reflections;
        DROP TABLE IF EXISTS confidence_state;
        DROP TABLE IF EXISTS system_settings;
        DROP TABLE IF EXISTS economic_experiments;
        DROP TABLE IF EXISTS agents;
        DROP TABLE IF EXISTS capital_pool;
        DROP TABLE IF EXISTS api_usage;
        DROP TABLE IF EXISTS market_signals;
        DROP TABLE IF EXISTS market_niches;
        DROP TABLE IF EXISTS market_proposals;
        """)

    # ================= CORE =================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal TEXT,
        plan_json TEXT,
        status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plan_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal TEXT,
        plan_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reflections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal TEXT,
        outcome TEXT,
        embedding TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS confidence_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER,
        autonomy TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ================= ECONOMIC =================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economic_experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        allocated_budget REAL,
        revenue REAL DEFAULT 0,
        cost REAL DEFAULT 0,
        status TEXT,
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
    CREATE TABLE IF NOT EXISTS capital_pool (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        total_capital REAL DEFAULT 10000,
        available_capital REAL DEFAULT 10000,
        reserved_capital REAL DEFAULT 0,
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

    # ================= MARKET =================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_tag TEXT,
            total_niches INTEGER,
            attack_count INTEGER,
            avg_cash_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
    

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT,
        source TEXT,
        signal_type TEXT,
        value REAL,
        week_tag TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_niches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT,
        week_tag TEXT,
        demand_score REAL,
        competition_score REAL,
        money_score REAL,
        urgency_score REAL,
        cash_score REAL,
        long_term_trend REAL,
        medium_term_trend REAL,
        short_term_spike REAL,
        status TEXT DEFAULT 'ANALYZED',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT,
        week _tag TEXT,
        cash_score REAL,
        proposed_budget REAL,
        status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

            # ================= DECISION MEMORY =================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_type TEXT,
            entity_id INTEGER,
            context_snapshot TEXT,
            reason TEXT,
            expected_outcome TEXT,
            actual_outcome TEXT,
            performance_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

    conn.commit()
    conn.close()

    print("✅ DB FULLY INITIALIZED")


if __name__ == "__main__":
    initialize_all_tables(reset=True)