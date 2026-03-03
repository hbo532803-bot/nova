class HumanGate:
    """
    Blocks execution until human approval.
    """

    def require_approval(self, plan: dict):
        if plan.get("autonomy_level") == "HUMAN_APPROVAL_REQUIRED":
            raise RuntimeError("WAITING FOR HUMAN APPROVAL")
