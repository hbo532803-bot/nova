from fastapi import BackgroundTasks
from backend.frontend_api.event_bus import broadcast


def log_event(message: str, level: str = "info", bg: BackgroundTasks | None = None):
    event = {
        "type": "log",
        "level": level,
        "message": message
    }

    # BackgroundTasks optional, but broadcast is sync-safe
    broadcast(event)
