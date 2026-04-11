from backend.database import get_db


def initialize_all_tables(reset: bool = False):
    with get_db() as conn:
        cursor = conn.cursor()

        try:

            if reset:

                cursor.executescript("""

                DROP TABLE IF EXISTS goals;
                DROP TABLE IF EXISTS plan_memory;
                DROP TABLE IF EXISTS reflections;
                DROP TABLE IF EXISTS confidence_state;
                DROP TABLE IF EXISTS system_settings;

                DROP TABLE IF EXISTS economic_experiments;
                DROP TABLE IF EXISTS capital_pool;
                DROP TABLE IF EXISTS agents;

                DROP TABLE IF EXISTS market_memory;
                DROP TABLE IF EXISTS market_signals;
                DROP TABLE IF EXISTS market_niches;
                DROP TABLE IF EXISTS market_proposals;

                DROP TABLE IF EXISTS decision_memory;
                DROP TABLE IF EXISTS agent_actions;
                DROP TABLE IF EXISTS nova_system_state;
                DROP TABLE IF EXISTS experiment_metrics;
                DROP TABLE IF EXISTS working_memory;
                DROP TABLE IF EXISTS knowledge_nodes;
                DROP TABLE IF EXISTS knowledge_edges;
                DROP TABLE IF EXISTS nova_commands;
                DROP TABLE IF EXISTS audit_log;
                DROP TABLE IF EXISTS agent_tasks;
                DROP TABLE IF EXISTS leads;
                DROP TABLE IF EXISTS traffic_metrics;
                DROP TABLE IF EXISTS revenue_events;

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
            CREATE TABLE IF NOT EXISTS reflections(               
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT,
                primary_goal TEXT,
                input_objective TEXT,
                execution_result TEXT,
                success INTEGER,
                confidence_before REAL,
                confidence_after REAL,
                embedding TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                score INTEGER DEFAULT 50,
                autonomy TEXT DEFAULT 'LIMITED_AUTONOMY',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            INSERT OR IGNORE INTO confidence_state (id) VALUES (1)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # ================= SYSTEM STATE =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS nova_system_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state TEXT NOT NULL,
                last_error TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            INSERT OR IGNORE INTO nova_system_state (id, state) VALUES (1, 'BOOTING')
            """)

            # ================= COMMAND QUEUE =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS nova_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_text TEXT,
                status TEXT DEFAULT 'PENDING',
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
            """)

            # ================= ECONOMY =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS economic_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                experiment_type TEXT,
                owner_agent TEXT,
                capital_allocated REAL DEFAULT 0,
                status TEXT DEFAULT 'IDEA',
                iteration INTEGER DEFAULT 0,
                validation_score REAL DEFAULT 0,
                revenue_generated REAL DEFAULT 0,
                cost_incurred REAL DEFAULT 0,
                cost_total REAL DEFAULT 0,
                cost_real_total REAL DEFAULT 0,
                cost_simulated_total REAL DEFAULT 0,
                cost_per_click REAL DEFAULT 0,
                cost_per_lead REAL DEFAULT 0,
                revenue_total REAL DEFAULT 0,
                revenue_real_payment REAL DEFAULT 0,
                revenue_estimated REAL DEFAULT 0,
                revenue_simulated REAL DEFAULT 0,
                revenue_source TEXT DEFAULT 'estimated',
                profit_total REAL DEFAULT 0,
                profit_per_user REAL DEFAULT 0,
                cac REAL DEFAULT 0,
                roi REAL DEFAULT 0,
                growth_rate REAL DEFAULT 0,
                cost_per_day REAL DEFAULT 0,
                cost_per_session REAL DEFAULT 0,
                capital_used REAL DEFAULT 0,
                capital_remaining REAL DEFAULT 0,
                capital_cap REAL DEFAULT 0,
                priority_score REAL DEFAULT 0,
                priority_level TEXT DEFAULT 'LOW',
                consecutive_losses INTEGER DEFAULT 0,
                last_tested DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_cost_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                source TEXT DEFAULT 'manual_input',
                cost_amount REAL DEFAULT 0,
                is_simulated INTEGER DEFAULT 0,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiment_cost_events_lookup
            ON experiment_cost_events(experiment_id, is_simulated, created_at)
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
            INSERT OR IGNORE INTO capital_pool (id) VALUES (1)
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
            CREATE INDEX IF NOT EXISTS idx_market_signals_week
                ON market_signals(week_tag)
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
            CREATE INDEX IF NOT EXISTS idx_market_niches_week
                ON market_niches(week_tag)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_name TEXT,
                week_tag TEXT,
                cash_score REAL,
                proposed_budget REAL,
                status TEXT DEFAULT 'PENDING',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # ================= INTELLIGENCE =================

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

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                action TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                task TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                metric_key TEXT,
                metric_value REAL,
                source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS working_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT,
                key TEXT,
                value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_working_memory_mission
            ON working_memory(mission_id)
            """)

            # ================= KNOWLEDGE GRAPH =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_type TEXT,
                node_key TEXT,
                data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(node_type, node_key)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                source_key TEXT,
                relation TEXT,
                target_type TEXT,
                target_key TEXT,
                weight REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # ================= AUDIT LOGGING =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor TEXT,
                action TEXT NOT NULL,
                target TEXT,
                payload TEXT,
                ip TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # ================= REVENUE EXECUTION =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                source TEXT,
                intent_level TEXT DEFAULT 'low',
                intent_score REAL DEFAULT 0,
                approved_for_contact INTEGER DEFAULT 0,
                last_interaction_source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_leads_mission_created
            ON leads(mission_id, created_at)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT,
                source TEXT,
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                leads INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0,
                lead_value REAL DEFAULT 200,
                estimated_revenue REAL DEFAULT 0,
                experiment_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_execution_actions_status
            ON execution_actions(status, experiment_id, created_at)
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversion_attempts_lookup
            ON conversion_attempts(lead_id, service_type, tier, status, created_at)
            """)

            default_offers = [
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
            for row in default_offers:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO offer_catalog
                    (service_type, tier, deliverables_json, expected_outcome, base_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    row,
                )

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_intelligence_lookup
            ON market_intelligence_events(platform, intent_level, category, created_at)
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user TEXT,
                command_text TEXT NOT NULL,
                mission_type TEXT DEFAULT 'general',
                parsed_json TEXT,
                status TEXT DEFAULT 'RECEIVED',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS revenue_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT,
                lead_id INTEGER,
                amount REAL DEFAULT 0,
                status TEXT DEFAULT 'PENDING',
                source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_signal_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                experiment_id INTEGER,
                event_type TEXT NOT NULL,
                source TEXT,
                session_id TEXT,
                event_value REAL,
                is_simulated INTEGER DEFAULT 0,
                reason TEXT,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_real_signal_lookup
            ON real_signal_events(mission_id, experiment_id, event_type, is_simulated, created_at)
            """)

            # ================= SOCIAL GROWTH =================

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_content_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                content_type TEXT NOT NULL,
                hook TEXT NOT NULL,
                body TEXT NOT NULL,
                cta TEXT NOT NULL,
                source_event_id INTEGER,
                status TEXT DEFAULT 'pending_approval',
                scheduled_for DATETIME,
                reviewed_by TEXT,
                reviewed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_content_status
            ON social_content_queue(status, platform, created_at)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_engagement_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                intent_level TEXT DEFAULT 'low',
                intent_score REAL DEFAULT 0,
                context_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_reply_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engagement_event_id INTEGER,
                lead_id INTEGER,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                message_type TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                status TEXT DEFAULT 'pending_approval',
                reviewed_by TEXT,
                reviewed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_reply_status
            ON social_reply_queue(status, platform, created_at)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                lead_profile TEXT NOT NULL,
                intent_level TEXT DEFAULT 'low',
                intent_score REAL DEFAULT 0,
                source_event_id INTEGER,
                status TEXT DEFAULT 'new',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_leads_intent
            ON social_leads(intent_level, platform, created_at)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_journey (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                experiment_id INTEGER,
                session_id TEXT NOT NULL,
                event_sequence INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                data_source TEXT DEFAULT 'real',
                traffic_source TEXT DEFAULT 'unknown',
                lead_quality TEXT,
                conversion_to_payment INTEGER,
                event_value REAL,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_journey_lookup
            ON session_journey(mission_id, experiment_id, session_id, event_sequence, created_at)
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiment_feedback_loops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                strategy_key TEXT,
                metrics_json TEXT,
                decision TEXT,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiment_feedback_experiment
            ON experiment_feedback_loops(experiment_id, created_at)
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_orders (
                id TEXT PRIMARY KEY,
                mission_id TEXT,
                user_input TEXT NOT NULL,
                service TEXT,
                requirement_json TEXT,
                offers_json TEXT,
                selected_plan TEXT,
                command_text TEXT,
                status TEXT DEFAULT 'PENDING',
                progress INTEGER DEFAULT 0,
                execution_result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_customer_orders_status_created
            ON customer_orders(status, created_at)
            """)

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e

    print("DB FULLY INITIALIZED")


if __name__ == "__main__":
    initialize_all_tables(reset=True)
