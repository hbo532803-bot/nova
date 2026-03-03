class CostGuard:
    """
    Tracks and enforces budget.
    """

    def __init__(self, max_budget: float):
        self.max_budget = max_budget
        self.used_budget = 0.0

    def charge(self, cost: float):
        if self.used_budget + cost > self.max_budget:
            raise RuntimeError("BUDGET EXCEEDED – execution blocked")

        self.used_budget += cost

    def status(self):
        return {
            "used": self.used_budget,
            "remaining": self.max_budget - self.used_budget
        }
