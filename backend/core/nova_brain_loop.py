import datetime

from backend.core.nova_core import get_nova_core
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.frontend_api.event_bus import broadcast
from backend.database import get_db
from backend.intelligence.self_improvement_engine import SelfImprovementEngine
from backend.memory.reflection_memory import ReflectionMemory
from backend.runtime.command_queue import CommandQueue
from backend.system.state_store import StateStore
from backend.core.cognitive_cycle import CognitiveCycle

class NovaBrainLoop:
    """
    Central autonomous loop of Nova.

    Responsibilities:
    - Observe system state
    - Decide strategic action
    - Execute via NovaCore
    - Run economic engine
    - Learn from results
    """

    def __init__(self):

        self.confidence = ConfidenceEngine()
        # Economic engine is executed via NovaCore/ExecutionEngine, never directly.
        self.self_improvement = SelfImprovementEngine()
        self.reflection = ReflectionMemory()
        self.commands = CommandQueue()
        self.state = StateStore()
        self.cognitive = CognitiveCycle()

    # -------------------------------------------------
    # MAIN CYCLE
    # -------------------------------------------------

    def run_cycle(self):

        state = self.confidence.get_state()
        learning = self.self_improvement.run_cycle()
        self.state.ensure()

        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Nova brain cycle started (confidence={state['score']})"
        })

        # 0️⃣ Command queue has priority (control console pipeline)
        pending = self.commands.fetch_pending()
        if pending:
            cmd = pending[0]
            cmd_id = cmd["id"]
            cmd_text = cmd["command_text"]

            core = get_nova_core()
            core.handle_command("__STATE__:PLANNING")
            self.commands.update_status(cmd_id, "RUNNING")

            core.handle_command("__STATE__:EXECUTING")
            result = core.handle_command(cmd_text)

            core.handle_command("__STATE__:LEARNING")
            self._record_reflection(cmd_text, state, result)
            self._learn(result)

            self.commands.update_status(cmd_id, "COMPLETED" if result.get("success") else "FAILED", result=str(result))
            core.handle_command("__STATE__:IDLE")

            return {"command_id": cmd_id, "command": cmd_text, "result": result, "learning": learning}

        # -------------------------------
        # 1️⃣ Observe system
        # -------------------------------
        cognitive = self.cognitive.run(goal_hint="autonomous mission")
        action = f"run mission autonomous mission"

        broadcast({
            "type": "log",
            "level": "think",
            "message": f"Nova decision: {action}"
        })

        # -------------------------------
        # 3️⃣ Execute via NovaCore (NO BYPASS)
        # -------------------------------

        # State transitions must be controlled by NovaBrainLoop
        core = get_nova_core()
        if "market" in action:
            core.handle_command("__STATE__:SCANNING_MARKET")
        else:
            core.handle_command("__STATE__:PLANNING")

        core.handle_command("__STATE__:EXECUTING")
        result = core.handle_command(action)
        core.handle_command("__STATE__:LEARNING")

        # -------------------------------
        # 4️⃣ Reflection learning (store results)
        # -------------------------------

        self._record_reflection(action, state, result)
        self._learn(result)

        core.handle_command("__STATE__:IDLE")

        return {
            "action": action,
            "result": result,
            "learning": learning,
        }

    # -------------------------------------------------
    # SYSTEM OBSERVATION
    # -------------------------------------------------

    def _observe(self):

        with get_db() as conn:
         cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(*) AS total
        FROM economic_experiments
        WHERE status NOT IN ('FAILED','ARCHIVED')
        """)

        active_experiments = cursor.fetchone()["total"]

        cursor.execute("""
        SELECT COUNT(*) AS pending
        FROM market_proposals
        WHERE status='PENDING'
        """)

        pending_proposals = cursor.fetchone()["pending"]

        conn.close()

        return {
            "active_experiments": active_experiments,
            "pending_proposals": pending_proposals
        }

    def _should_run_daily_market_scan(self) -> bool:
        """
        Guardrails: market scan interval = 24 hours.
        Store last scan timestamp in system_settings to avoid file-based state.
        """
        now = datetime.datetime.utcnow()

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM system_settings WHERE key = ?",
                ("last_market_scan_utc",),
            )
            row = cursor.fetchone()

            if not row or not row["value"]:
                cursor.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, ?)",
                    ("last_market_scan_utc", now.isoformat(), now),
                )
                conn.commit()
                return True

            try:
                last = datetime.datetime.fromisoformat(str(row["value"]))
            except Exception:
                last = now - datetime.timedelta(days=365)

            if (now - last) >= datetime.timedelta(hours=24):
                cursor.execute(
                    "UPDATE system_settings SET value = ?, updated_at = ? WHERE key = ?",
                    (now.isoformat(), now, "last_market_scan_utc"),
                )
                conn.commit()
                return True

        return False

    # -------------------------------------------------
    # DECISION ENGINE
    # -------------------------------------------------

    def _decide_action(self, state, observation):

        confidence = state["score"]

        active_exp = observation["active_experiments"]

        pending_prop = observation["pending_proposals"]

        # System stabilization
        if confidence < 60:
            return "analyze system"

        # Daily market intelligence (guarded by 24h interval)
        if self._should_run_daily_market_scan():
            return "analyze market"

        # Expand experiments
        if confidence > 80 and active_exp < 3:
            return "expand experiments"

        # Default
        return "optimize strategy"

    # -------------------------------------------------
    # LEARNING SYSTEM
    # -------------------------------------------------

    def _learn(self, result):

        try:

            if result.get("success"):

                self.confidence.adjust(+1)

            else:

                self.confidence.adjust(-1)

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "warn",
                "message": f"Learning update failed: {e}"
            })

    def _record_reflection(self, action: str, state: dict, result: dict):
        try:
            self.reflection.record_reflection(
                {
                    "cycle_id": str(datetime.datetime.utcnow().timestamp()),
                    "primary_goal_snapshot": action,
                    "input_objective": action,
                    "execution_result": str(result),
                    "success": bool(result.get("success") or result.get("decision", {}).get("success")),
                    "confidence_before": state.get("score"),
                    "confidence_after": state.get("score"),
                }
            )
        except Exception as e:
            broadcast(
                {
                    "type": "log",
                    "level": "warn",
                    "message": f"Reflection record failed: {e}",
                }
            )