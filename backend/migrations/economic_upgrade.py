from backend.database import get_db


def upgrade_economic_schema() -> None:
    with get_db() as conn:
        cursor = conn.cursor()

        columns = {
            "capital_allocated": "REAL DEFAULT 0",
            "cost_incurred": "REAL DEFAULT 0",
            "revenue_generated": "REAL DEFAULT 0",
            "roi": "REAL DEFAULT 0",
            "consecutive_losses": "INTEGER DEFAULT 0",
            "cost_total": "REAL DEFAULT 0",
            "cost_real_total": "REAL DEFAULT 0",
            "cost_simulated_total": "REAL DEFAULT 0",
            "cost_per_click": "REAL DEFAULT 0",
            "cost_per_lead": "REAL DEFAULT 0",
            "revenue_total": "REAL DEFAULT 0",
            "revenue_real_payment": "REAL DEFAULT 0",
            "revenue_estimated": "REAL DEFAULT 0",
            "revenue_simulated": "REAL DEFAULT 0",
            "revenue_source": "TEXT DEFAULT 'estimated'",
            "profit_total": "REAL DEFAULT 0",
            "profit_per_user": "REAL DEFAULT 0",
            "cac": "REAL DEFAULT 0",
            "growth_rate": "REAL DEFAULT 0",
            "cost_per_day": "REAL DEFAULT 0",
            "cost_per_session": "REAL DEFAULT 0",
            "capital_used": "REAL DEFAULT 0",
            "capital_remaining": "REAL DEFAULT 0",
            "capital_cap": "REAL DEFAULT 0",
            "priority_score": "REAL DEFAULT 0",
            "priority_level": "TEXT DEFAULT 'LOW'",
        }

        for column, definition in columns.items():
            try:
                cursor.execute(f"ALTER TABLE economic_experiments ADD COLUMN {column} {definition}")
            except Exception:
                pass

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiment_cost_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                source TEXT DEFAULT 'manual_input',
                cost_amount REAL DEFAULT 0,
                is_simulated INTEGER DEFAULT 0,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_experiment_cost_events_lookup
            ON experiment_cost_events(experiment_id, is_simulated, created_at)
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_type TEXT UNIQUE,
                success_rate REAL DEFAULT 0,
                avg_profit REAL DEFAULT 0,
                sample_size INTEGER DEFAULT 0,
                niche TEXT,
                traffic_source TEXT,
                funnel_type TEXT,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for col, col_type in {
            "intent_level": "TEXT DEFAULT 'low'",
            "intent_score": "REAL DEFAULT 0",
            "approved_for_contact": "INTEGER DEFAULT 0",
            "last_interaction_source": "TEXT",
        }.items():
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type}")
            except Exception:
                pass

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                action_type TEXT NOT NULL,
                channel TEXT,
                payload_json TEXT,
                status TEXT DEFAULT 'PENDING',
                requires_approval INTEGER DEFAULT 0,
                approved_by TEXT,
                approved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_execution_actions_status
            ON execution_actions(status, experiment_id, created_at)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS communication_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                experiment_id INTEGER,
                channel TEXT,
                message_body TEXT,
                status TEXT DEFAULT 'PENDING_APPROVAL',
                approved_by TEXT,
                approved_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        for col, col_type in {
            "niche": "TEXT",
            "traffic_source": "TEXT",
            "funnel_type": "TEXT",
        }.items():
            try:
                cursor.execute(f"ALTER TABLE strategy_patterns ADD COLUMN {col} {col_type}")
            except Exception:
                pass
        conn.commit()
