class KillSwitch:
    """
    Emergency shutdown.
    """

    def __init__(self):
        self.active = False

    def activate(self):
        self.active = True

    def check(self):
        if self.active:
            raise RuntimeError("KILL SWITCH ACTIVE – system stopped")
    def is_triggered(self):   # 👈 YE ADD KARO
        return self.is_triggered

# 🔒 Singleton Instance
kill_switch = KillSwitch()

