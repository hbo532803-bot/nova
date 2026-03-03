from backend.execution.hardened_executor import hardened_execute





def entry_gate(plan: dict):
    """
    🚪 ENTRY GATE
    Execution se pehle final safety check
    """

    # 1. Mandatory planner fields
    required_fields = [
        "assumed_failure",
        "failure_impact",
        "confidence_score"
    ]

    for field in required_fields:
        if field not in plan:
            raise RuntimeError(f"ENTRY GATE BLOCKED: missing '{field}'")

    # 2. Confidence gate
    confidence = plan["confidence_score"]

    if confidence < 50:
        raise RuntimeError("ENTRY GATE BLOCKED: confidence < 50 (planning only)")

    if 50 <= confidence < 70:
        raise RuntimeError(
            "ENTRY GATE BLOCKED: confidence 50–70 requires human permission"
        )
    plan.setdefault("_permission_context", {
        "session": "default",
        "source": "entry_gate"
    })
    # 3. Safe execution
    return hardened_execute(plan)
