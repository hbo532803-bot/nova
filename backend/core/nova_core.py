import threading
from datetime import datetime

from backend.agents.supervisor import SupervisorAgent
from backend.frontend_api.event_bus import broadcast
from backend.database import get_db


class NovaCore:
    """
    Central decision brain of Nova.
    All commands (user or autonomous) must pass here.
    """

    def __init__(self):

        self.supervisor = SupervisorAgent()

        # Prevent concurrent execution collisions
        self._lock = threading.Lock()

        # Nova runtime state
        self.last_command = None
        self.last_result = None

    # ====================================
    # PUBLIC ENTRYPOINT
    # ====================================

    def handle_command(self, command: str):

        with self._lock:

            self.last_command = command

            broadcast({
                "type": "log",
                "level": "info",
                "message": f"NovaCore received command: {command}"
            })

            plan = self._create_plan(command)

            result = self._execute(plan)

            self.last_result = result

            self._log_decision(plan, result)

            return result

    # ====================================
    # PLAN CREATION
    # ====================================

    def _create_plan(self, command: str):

        plan = {
            "goal": command,
            "steps": [],
            "autonomy_level": "LIMITED_AUTONOMY",
            "_permission_context": "nova_core",
            "created_at": datetime.utcnow().isoformat()
        }

        cmd = command.lower()

        if "analyze" in cmd:

            plan["steps"] = ["analyze"]

        elif "optimize" in cmd:

            plan["steps"] = ["analyze", "execute"]

        elif "market" in cmd:

            plan["steps"] = ["market_scan"]

        elif "experiment" in cmd:

            plan["steps"] = ["experiment"]

        else:

            plan["steps"] = ["execute"]

        return plan

    # ====================================
    # EXECUTION
    # ====================================

    def _execute(self, plan):

        try:

            broadcast({
                "type": "log",
                "level": "think",
                "message": "Supervisor executing plan"
            })

            result = self.supervisor.handle(plan)

            broadcast({
                "type": "log",
                "level": "info",
                "message": "Plan executed successfully"
            })

            return result

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "error",
                "message": f"Execution failed: {e}"
            })

            return {
                "success": False,
                "error": str(e)
            }

    # ====================================
    # DECISION MEMORY
    # ====================================

    def _log_decision(self, plan, result):

        try:

            with get_db() as conn:
             cursor = conn.cursor()

             cursor.execute(
                """
                INSERT INTO decision_memory
                (decision_type, context_snapshot, actual_outcome, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "nova_core",
                    str(plan),
                    str(result),
                    datetime.utcnow().isoformat()
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "warn",
                "message": f"Decision logging failed: {e}"
            })


# Global singleton
nova_core = NovaCore()