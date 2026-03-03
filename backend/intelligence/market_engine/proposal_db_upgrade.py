import sqlite3
from pathlib import Path

DB_PATH = Path("backend/nova.db")

def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        niche_name TEXT,
        week_tag TEXT,
        cash_score REAL,
        proposed_budget REAL DEFAULT 0,
        status TEXT DEFAULT 'PENDING',  -- PENDING / APPROVED / REJECTED
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Proposal table ready")

if __name__ == "__main__":
    upgrade()