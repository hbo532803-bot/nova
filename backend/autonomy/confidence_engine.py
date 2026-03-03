from backend.frontend_api.event_bus import broadcast

class ConfidenceEngine:
    def __init__(self):
        self.score = 50
        self.autonomy = "MANUAL"

    def _update_autonomy(self):
        if self.score < 40:
            self.autonomy = "RESTRICTED"
        elif self.score < 60:
            self.autonomy = "ASSISTED"
        elif self.score < 85:
            self.autonomy = "LIMITED"
        else:
            self.autonomy = "EXPANDED"

    def adjust(self, delta: int):
        self.score += delta
        self.score = max(0, min(100, self.score))
        self._update_autonomy()

        broadcast({
            "type": "confidence_update",
            "score": self.score,
            "autonomy": self.autonomy
        })

    def success(self):
        self.adjust(3)

    def failure(self):
        self.adjust(-5)


confidence = ConfidenceEngine()
