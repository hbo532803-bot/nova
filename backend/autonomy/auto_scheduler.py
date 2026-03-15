import time
import threading

from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.core.nova_brain_loop import NovaBrainLoop
from backend.frontend_api.event_bus import broadcast


class AutoScheduler:

    def __init__(self):

        self.running = False
        self.thread = None

        self.confidence = ConfidenceEngine()
        self.brain = NovaBrainLoop()

        self.last_cycle = None

    # ----------------------------
    # Dynamic Interval Based on Confidence
    # ----------------------------
    def dynamic_interval(self):

        score = self.confidence.get_score()

        if score < 60:
            return 60

        elif score < 75:
            return 30

        elif score < 85:
            return 15

        else:
            return 5

    # ----------------------------
    # Scheduler Loop
    # ----------------------------
    def _loop(self):

        broadcast({
            "type": "log",
            "level": "info",
            "message": "AutoScheduler started"
        })

        while self.running:

            try:

                result = self.brain.run_cycle()

                self.last_cycle = result

            except Exception as e:

                broadcast({
                    "type": "log",
                    "level": "error",
                    "message": f"AutoScheduler error: {e}"
                })

            time.sleep(self.dynamic_interval())

        broadcast({
            "type": "log",
            "level": "warn",
            "message": "AutoScheduler stopped"
        })

    # ----------------------------
    # Start Scheduler
    # ----------------------------
    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._loop,
            daemon=True
        )

        self.thread.start()

    # ----------------------------
    # Stop Scheduler
    # ----------------------------
    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)