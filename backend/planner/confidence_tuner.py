from typing import Dict, List


class ConfidenceTuner:
    """
    Adjusts confidence based on past execution truth.
    """

    def tune(self, base_confidence: int, logs: List[Dict]) -> int:
        if not logs:
            return base_confidence

        penalty = 0
        recent_logs = logs[-10:]  # last 10 executions

        failures = sum(1 for l in recent_logs if not l.get("success"))
        rollbacks = sum(1 for l in recent_logs if l.get("rolled_back"))

        penalty += failures * 5
        penalty += rollbacks * 3

        tuned = max(0, base_confidence - penalty)
        return tuned
