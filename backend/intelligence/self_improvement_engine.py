from backend.database import get_db
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.frontend_api.event_bus import broadcast


class SelfImprovementEngine:

    FAILURE_THRESHOLD = 3
    SUCCESS_THRESHOLD = 2

    def __init__(self):

        self.confidence = ConfidenceEngine()

    def run_cycle(self):

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Self improvement cycle started"
        })

        reflections = self.collect_reflections()

        analysis = self.analyze_patterns(reflections)

        adjustments = self.apply_learning(analysis)

        return {
            "reflections": len(reflections),
            "analysis": analysis,
            "adjustments": adjustments
        }

    def collect_reflections(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, name, roi, consecutive_losses
            FROM economic_experiments
            WHERE status IN ('FAILED','SCALING')
            """)

            rows = cursor.fetchall()

        reflections = []

        for r in rows:

            reflections.append({
                "experiment_id": r["id"],
                "name": r["name"],
                "roi": r["roi"],
                "losses": r["consecutive_losses"]
            })

        return reflections

    def analyze_patterns(self, reflections):

        success = 0
        failures = 0

        for r in reflections:

            if r["roi"] > 0:
                success += 1
            else:
                failures += 1

        return {
            "success_count": success,
            "failure_count": failures
        }

    def apply_learning(self, analysis):

        adjustments = []

        success = analysis["success_count"]
        failures = analysis["failure_count"]

        if failures >= self.FAILURE_THRESHOLD:

            self.confidence.adjust(-2)

            adjustments.append("confidence_decreased")

        if success >= self.SUCCESS_THRESHOLD:

            self.confidence.adjust(+2)

            adjustments.append("confidence_increased")

        return adjustments