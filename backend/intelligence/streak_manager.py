from dataclasses import dataclass
from backend.frontend_api.event_bus import broadcast

MAX_STREAK = 3


@dataclass
class StreakState:

    active: bool = False
    count: int = 0

    def start(self):

        self.active = True
        self.count = 0

        broadcast({
            "type": "streak",
            "state": "started",
            "count": self.count
        })

    def step(self, reason: str):

        if not self.active:
            return

        self.count += 1

        broadcast({
            "type": "streak",
            "state": "step",
            "count": self.count,
            "reason": reason
        })

        if self.count >= MAX_STREAK:
            self.stop("max_streak_reached")

    def stop(self, reason: str):

        broadcast({
            "type": "streak",
            "state": "stopped",
            "count": self.count,
            "reason": reason
        })

        self.active = False
        self.count = 0


streak = StreakState()