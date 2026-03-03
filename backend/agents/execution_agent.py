from backend.agents.base_agent import BaseAgent
from backend.execution.hardened_executor import hardened_execute
# --- PATCH START (agent uses system access helpers) ---
from backend.system.file_reader import read_file
from backend.system.file_editor import propose_edit
from backend.system.command_runner import run_command
# --- PATCH END ---


class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExecutionAgent")

    def can_handle(self, plan: dict) -> bool:
        return "execute" in plan.get("steps", [])

    def execute(self, plan: dict) -> dict:
        result = hardened_execute(plan)
        return {
            "agent": self.name,
            "result": result,
            "success": result.success
        }
