class AutonomyManager:
    """
    Controls how much freedom planner has.
    """

    def autonomy_level(self, confidence: int) -> str:
        if confidence < 50:
            return "PLANNING_ONLY"
        elif confidence < 70:
            return "HUMAN_APPROVAL_REQUIRED"
        elif confidence < 85:
            return "LIMITED_AUTONOMY"
        else:
            return "EXPANSION_SUGGESTION_ONLY"
