from backend.frontend_api.event_bus import broadcast

class PlanningBrain:

    def decompose(self, goal: str):
        """
        Break goal into structured plan.
        """
        broadcast({
            "type": "log",
            "level": "think",
            "message": "Brain: Analyzing goal deeply"
        })

        steps = [
            {"step": "Clarify intent", "risk": 1},
            {"step": "Identify required changes", "risk": 3},
            {"step": "Check system safety impact", "risk": 4},
            {"step": "Propose minimal safe improvement", "risk": 2},
        ]

        return steps

    def prioritize(self, steps):
        """
        Sort by lowest risk first.
        """
        return sorted(steps, key=lambda x: x["risk"])

    def self_review(self, outcome):
        """
        Evaluate if execution improved system.
        """
        broadcast({
            "type": "log",
            "level": "think",
            "message": "Brain: Performing self-review"
        })

        if outcome.get("auto_apply"):
            return "positive"
        return "neutral"


brain = PlanningBrain()
