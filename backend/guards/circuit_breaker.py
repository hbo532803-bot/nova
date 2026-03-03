class CircuitBreaker:
    """
    Stops system after repeated failures.
    """

    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self.failures = 0

    def record(self, success: bool):
        if success:
            self.failures = 0
        else:
            self.failures += 1

        if self.failures >= self.max_failures:
            raise RuntimeError("CIRCUIT OPEN – system halted")
