import time
import threading
from backend.intelligence.confidence_engine import ConfidenceEngine


class AutoScheduler:

    def __init__(self, controller):
        # Controller inject karo yahin
        self.controller = controller
        self.running = False
        self.thread = None

    # ----------------------------
    # Dynamic Interval Based on Confidence
    # ----------------------------
    def dynamic_interval(self):

        engine = ConfidenceEngine()
        score = engine.get_score()

        # Lower confidence → slower cycles
        if score < 60:
            return 60  # 1 min

        elif score < 75:
            return 30  # 30 sec

        elif score < 85:
            return 15  # 15 sec

        else:
            return 5   # high confidence → faster loop

    # ----------------------------
    # Loop
    # ----------------------------
    def _loop(self):

        while self.running:
            try:
                if self.controller:
                    self.controller.run_full_cycle()
            except Exception as e:
                print("AutoScheduler error:", e)

            time.sleep(self.dynamic_interval())

    # ----------------------------
    # Start
    # ----------------------------
    def start(self):

        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    # ----------------------------
    # Stop
    # ----------------------------
    def stop(self):

        self.running = False