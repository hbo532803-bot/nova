from backend.database import get_db
from threading import Lock


_db_init_lock = Lock()
_db_initialized = False


def _schema_present(cursor) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name IN ('goals', 'nova_commands', 'working_memory')
        LIMIT 1
        """
    )
    return cursor.fetchone() is not None


def initialize_all_tables(reset: bool = False):
    global _db_initialized

    with _db_init_lock:
        if _db_initialized and not reset:
            return False

        with get_db() as conn:
            cursor = conn.cursor()
            if not reset and _schema_present(cursor):
                _db_initialized = True
                return False

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
                roi REAL DEFAULT 0,
                consecutive_losses INTEGER DEFAULT 0,
                last_tested DATETIME,
                notes TEXT,
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

                conn.commit()

            except Exception as e:
                conn.rollback()
                raise e

        _db_initialized = True
        print("DB FULLY INITIALIZED")
        return True


if __name__ == "__main__":
    initialize_all_tables(reset=True)
