from backend.memory.goal_memory import primary_goal
from backend.intelligence.ethics_gate import check
from backend.intelligence.llm_engine import run_llm_reasoning
from backend.intelligence.decision_router import route_decision
from backend.tools.diff_engine import apply_change
from backend.frontend_api.event_bus import broadcast
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.autonomy.cooldown import cooldown


def autonomous_cycle():
    pg = primary_goal()

    if not pg:
        return

    goal = pg["goal"]

    if not cooldown.can_run():
        return

    broadcast({
        "type": "log",
        "level": "info",
        "message": "Autonomous cycle triggered"
    })

    ok, reason = check(goal)
    if not ok:
        broadcast({
            "type": "log",
            "level": "warn",
            "message": f"Autonomy blocked by ethics: {reason}"
        })
        return

    decision = run_llm_reasoning({"goal": goal})

    outcome = route_decision(decision)

    if outcome.get("auto_apply"):
        apply_change(outcome["path"], outcome["content"])
        ConfidenceEngine.success()
        broadcast({
            "type": "log",
            "level": "info",
            "message": "Autonomous improvement applied"
        })

    cooldown.mark_run()
