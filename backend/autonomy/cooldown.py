import time

class Cooldown:
    def __init__(self):
        self.last_run = 0
        self.cooldown_seconds = 20  # prevent rapid loops

    def can_run(self):
        return time.time() - self.last_run > self.cooldown_seconds

    def mark_run(self):
        self.last_run = time.time()


cooldown = Cooldown()
    