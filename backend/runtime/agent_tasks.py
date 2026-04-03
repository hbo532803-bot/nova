from backend.tools.tool_sandbox import ToolSandbox
from backend.tools.web_access import safe_get
from backend.tools.sandbox_shell import safe_execute

from backend.database import get_db
from backend.db_retry import run_db_write_with_retry


class AgentTaskRunner:

    def __init__(self):

        self.sandbox = ToolSandbox(timeout_sec=5)

    # ---------------------------------
    # RUN TASK
    # ---------------------------------

    def run_task(self, agent_id, task):

        task_text = task["task"].lower()

        result = None

        try:

            # ------------------------------
            # RESEARCH TASK
            # ------------------------------

            if "research" in task_text:

                result = self.sandbox.run(
                    safe_get,
                    "https://api.github.com"
                )

            # ------------------------------
            # SHELL TASK
            # ------------------------------

            elif "deploy" in task_text or "test" in task_text:

                result = self.sandbox.run(
                    safe_execute,
                    "echo deployment check"
                )

            else:

                result = {"info": "task simulated"}

        except Exception as e:

            result = {"error": str(e)}

        self._store_action(agent_id, task["task"], result)

        return result

    # ---------------------------------
    # STORE ACTION
    # ---------------------------------

    def _store_action(self, agent_id, action, result):
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_actions
                (agent_name, action, result)
                VALUES (?, ?, ?)
                """,
                (str(agent_id), action, str(result)),
            )
            conn.commit()
            return None

        run_db_write_with_retry("agent_actions.insert.task", _write)