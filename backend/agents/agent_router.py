from backend.execution.hardened_executor import hardened_execute

def route_plan(plan: dict):
    """
    Single routing point.
    """
    return hardened_execute(plan)
