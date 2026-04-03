"""
Hardened execution wrapper.
Normalizes legacy executor output.
"""

from backend.execution.executor import execute_plan


def hardened_execute(plan: dict):
    raw = execute_plan(plan)

    if raw is None:
        return {
            "success": False,
            "error": "Executor returned None",
            "data": None,
        }

    if isinstance(raw, dict):
        raw.setdefault("success", True)
        return raw

    return {
        "success": True,
        "data": raw,
    }
