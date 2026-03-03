import json
import time
from pathlib import Path
from backend.frontend_api.event_bus import broadcast

MEMORY_PATH = Path("backend/memory/goals.json")
MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)

def _load():
    if not MEMORY_PATH.exists():
        return []
    return json.loads(MEMORY_PATH.read_text())

def _save(goals):
    MEMORY_PATH.write_text(json.dumps(goals, indent=2))

def remember(goal: str, source: str = "human", priority: int = 5):
    goals = _load()

    # prevent exact duplicates
    for g in goals:
        if g["goal"].lower() == goal.lower() and g["active"]:
            broadcast({
                "type": "memory",
                "action": "duplicate_ignored",
                "goal": goal
            })
            return g

    # deactivate all other primary goals
    for g in goals:
        if g.get("primary"):
            g["primary"] = False

    entry = {
        "id": int(time.time() * 1000),
        "goal": goal,
        "source": source,
        "priority": priority,
        "ts": time.time(),
        "active": True,
        "primary": True
    }

    goals.append(entry)
    _save(goals)

    broadcast({
        "type": "memory",
        "action": "primary_set",
        "entry": entry
    })

    return entry

def list_goals():
    return _load()

def primary_goal():
    goals = _load()
    for g in goals:
        if g.get("primary") and g["active"]:
            return g
    return None
