import threading

from backend.agents.supervisor import SupervisorAgent
from backend.frontend_api.event_bus import broadcast
from backend.db_init import get_connection


class NovaCore:
    """
    Central decision brain of Nova.
    All commands (user or autonomous) should go through this class.
    """

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self._lock = threading.Lock()

    # ==========================
    # PUBLIC ENTRYPOINT
    # ==========================

    def handle_command(self, command: str):

        with self._lock:

            broadcast({
                "type": "log",
                "level": "info",
                "message": f"NovaCore received command: {command}"
            })

            plan = self._create_plan(command)

            result = self._execute(plan)

            self._log_decision(plan, result)

            return result

    # ==========================
    # PLAN CREATION
    # ==========================

    def _create_plan(self, command: str):

        plan = {
            "goal": command,
            "steps": [],
            "autonomy_level": "LIMITED_AUTONOMY",
            "_permission_context": "nova_core"
        }

        if "analyze" in command:
            plan["steps"] = ["analyze"]

        elif "optimize" in command:
            plan["steps"] = ["analyze", "execute"]

        else:
            plan["steps"] = ["execute"]

        return plan

    # ==========================
    # EXECUTION
    # ==========================

    def _execute(self, plan):

        try:

            result = self.supervisor.handle(plan)

            broadcast({
                "type": "log",
                "level": "info",
                "message": "Plan executed via Supervisor"
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

    # ==========================
    # DECISION MEMORY
    # ==========================

    def _log_decision(self, plan, result):

        try:

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO decision_memory
                (decision_type, context_snapshot, actual_outcome)
                VALUES (?, ?, ?)
                """,
                (
                    "nova_core",
                    str(plan),
                    str(result)
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


# Global instance
nova_core = NovaCore()