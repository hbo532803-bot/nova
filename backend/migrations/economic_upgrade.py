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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS offer_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_type TEXT NOT NULL,
                tier TEXT NOT NULL,
                deliverables_json TEXT NOT NULL,
                expected_outcome TEXT,
                base_price REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                UNIQUE(service_type, tier)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversion_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                experiment_id INTEGER,
                service_type TEXT NOT NULL,
                tier TEXT NOT NULL,
                offer_payload_json TEXT,
                proposed_price REAL DEFAULT 0,
                status TEXT DEFAULT 'DRAFT',
                approved_by TEXT,
                approved_at DATETIME,
                converted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversion_attempts_lookup
            ON conversion_attempts(lead_id, service_type, tier, status, created_at)
            """
        )
        defaults = [
            ("website_development", "basic", '["single-page site","contact form","mobile-ready"]', "Launch a credible online presence", 1200.0),
            ("website_development", "standard", '["5-page website","basic SEO","analytics setup"]', "Generate qualified inbound leads", 2800.0),
            ("website_development", "premium", '["conversion funnel","advanced SEO","CRM integration"]', "Maximize conversion and revenue readiness", 5500.0),
            ("lead_generation", "basic", '["1 channel setup","lead capture form","weekly report"]', "Start predictable lead flow", 900.0),
            ("lead_generation", "standard", '["multi-channel outreach plan","qualification workflow","dashboard"]', "Increase qualified lead volume", 2200.0),
            ("lead_generation", "premium", '["omnichannel engine","intent scoring","conversion optimization"]', "Scale high-intent pipeline", 4800.0),
            ("automation", "basic", '["1 workflow automation","error alerts","handover doc"]', "Reduce repetitive tasks", 1500.0),
            ("automation", "standard", '["3 workflow automations","CRM sync","monitoring"]', "Improve operating efficiency", 3200.0),
            ("automation", "premium", '["end-to-end automation architecture","governance controls","training"]', "Create scalable autonomous operations", 6800.0),
        ]
        for r in defaults:
            cursor.execute(
                """
                INSERT OR IGNORE INTO offer_catalog
                (service_type, tier, deliverables_json, expected_outcome, base_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                r,
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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS market_intelligence_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                source_url TEXT,
                author_handle TEXT,
                content TEXT,
                intent_level TEXT DEFAULT 'low',
                intent_score REAL DEFAULT 0,
                category TEXT DEFAULT 'lead_generation',
                urgency_score REAL DEFAULT 0,
                problem_summary TEXT,
                is_simulated INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_intelligence_lookup
            ON market_intelligence_events(platform, intent_level, category, created_at)
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_event_id INTEGER,
                platform TEXT,
                category TEXT,
                intent_level TEXT DEFAULT 'low',
                intent_score REAL DEFAULT 0,
                urgency_score REAL DEFAULT 0,
                confidence_score REAL DEFAULT 0,
                problem_statement TEXT,
                status TEXT DEFAULT 'NEW',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user TEXT,
                command_text TEXT NOT NULL,
                mission_type TEXT DEFAULT 'general',
                parsed_json TEXT,
                status TEXT DEFAULT 'RECEIVED',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mission_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id INTEGER,
                goal TEXT,
                mission_type TEXT,
                required_capabilities_json TEXT,
                actions_json TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                experiment_id INTEGER,
                channel TEXT,
                user_message TEXT,
                assistant_suggestion TEXT,
                context_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()
