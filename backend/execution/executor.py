"""
LEGACY EXECUTOR
This file guarantees execute_plan() exists.
Old logic can live inside _legacy_execute().
"""

def _legacy_execute(plan: dict):
    """
    Tumhara purana execution logic yahan ho sakta hai.
    Abhi ke liye safe stub.
    """
    return {
        "success": True,
        "data": plan,
        "message": "Legacy executor stub executed"
    }


def execute_plan(plan: dict):
    """
    Stable public API.
    Hardened executor isi ko call karega.
    """
    return _legacy_execute(plan)
