class KillSwitch:
    """
    Emergency shutdown controller for Nova system.
    """

    def __init__(self):
        self.active = False

    # -----------------------------
    # Trigger system stop
    # -----------------------------
    def trigger(self):
        self.active = True

    # -----------------------------
    # Resume system
    # -----------------------------
    def reset(self):
        self.active = False

    # -----------------------------
    # Internal check
    # -----------------------------
    def check(self):
        if self.active:
            raise RuntimeError("KILL SWITCH ACTIVE – system stopped")

    # -----------------------------
    # Status
    # -----------------------------
    def is_triggered(self):
        return self.active


# Singleton
kill_switch = KillSwitch()