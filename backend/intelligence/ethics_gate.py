from backend.frontend_api.event_bus import broadcast


FORBIDDEN = [
    "delete everything",
    "self destruct",
    "bypass permission",
]


def check(goal: str):

    lowered = goal.lower()

    for rule in FORBIDDEN:

        if rule in lowered:

            reason = f"Blocked by ethics rule: '{rule}'"

            broadcast({
                "type": "ethics",
                "allowed": False,
                "reason": reason
            })

            return False, reason

    broadcast({
        "type": "ethics",
        "allowed": True,
        "reason": "Goal passes ethics checks"
    })

    return True, "ok"