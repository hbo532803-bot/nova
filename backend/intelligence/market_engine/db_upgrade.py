import sqlite3
from pathlib import Path

DB_PATH = Path("backend/nova.db")

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -----------------------------
    # Market Niches Table
    # -----------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_niches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT NOT NULL,
        week_tag TEXT NOT NULL,
        demand_score REAL,
        competition_score REAL,
        money_score REAL,
        urgency_score REAL,
        cash_score REAL,
        long_term_trend REAL,
        medium_term_trend REAL,
        short_term_spike REAL,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Raw Signals Table
    # -----------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT,
        source TEXT,
        signal_type TEXT,
        value REAL,
        week_tag TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Market Decisions Log
    # -----------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT,
        decision TEXT,
        reason TEXT,
        week_tag TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    print("✅ Market Engine DB Upgrade Completed")

if __name__ == "__main__":
    upgrade()