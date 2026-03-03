class AgentBlacklist:
    """
    Blocks agents that repeatedly fail.
    """

    def __init__(self, threshold: int = 30):
        self.threshold = threshold
        self.blacklisted = set()

    def evaluate(self, agent):
        if agent.trust_score < self.threshold:
            self.blacklisted.add(agent.name)

    def is_blocked(self, agent) -> bool:
        return agent.name in self.blacklisted
