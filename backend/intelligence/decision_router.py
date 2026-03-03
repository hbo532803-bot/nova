from backend.system.permission_gate import permission_gate
from backend.frontend_api.event_bus import broadcast
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.risk_classifier import classify_change
confidence = ConfidenceEngine()

def route_decision(decision: dict, *, diff_ctx: dict | None = None):
    """
    Routes decisions with autonomy awareness.
    diff_ctx = { "path": str, "diff": list[str] } when applicable
    """

    # ---- PERMISSION ----
    if decision.get("needs_permission"):
        p = decision["permission"]
        try:
            permission_gate.request(
                action=p["action"],
                target=p["target"],
                reason=p["reason"]
            )
        except RuntimeError:
            broadcast({
                "type": "permission_request",
                "action": p["action"],
                "target": p["target"],
                "reason": p["reason"]
            })
            return {"blocked": "permission"}

    # ---- DIFF AUTONOMY ----
    if decision.get("needs_diff") and diff_ctx:
        risk = classify_change(diff_ctx["path"], diff_ctx["diff"])

        if risk == "LOW" and ConfidenceEngine.autonomy == "LIMITED":
            broadcast({
                "type": "log",
                "level": "info",
                "message": "Auto-applying low-risk change (LIMITED autonomy)"
            })
            return {"auto_apply": True}

        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Diff requires human approval (risk={risk}, autonomy={ConfidenceEngine.autonomy})"
        })
        return {"blocked": "diff"}

    return {"ok": True}
