# backend/migrations/economic_upgrade.py

from backend.database import get_db


def upgrade_economic_schema():
    with get_db() as conn:
     cursor = conn.cursor()

    # Add new columns safely
    columns = {
        "capital_allocated": "REAL DEFAULT 0",
        "cost_incurred": "REAL DEFAULT 0",
        "revenue_generated": "REAL DEFAULT 0",
        "roi": "REAL DEFAULT 0",
        "consecutive_losses": "INTEGER DEFAULT 0"
    }

    for column, definition in columns.items():
        try:
            cursor.execute(f"""
                ALTER TABLE economic_experiments
                ADD COLUMN {column} {definition}
            """)
        except Exception:
            pass  # Column may already exist

    conn.commit()
 