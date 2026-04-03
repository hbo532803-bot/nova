from abc import ABC, abstractmethod
from typing import Dict


class BaseAgent(ABC):
    """
    Every agent MUST follow this contract.
    """

    def __init__(self, name: str):
        self.name = name
        self.trust_score = 70  # default neutral
        self.capabilities: set[str] = set()

    @abstractmethod
    def can_handle(self, plan: Dict) -> bool:
        pass

    @abstractmethod
    def execute(self, plan: Dict) -> Dict:
        pass

    def adjust_trust(self, success: bool):
        if success:
            self.trust_score = min(100, self.trust_score + 2)
        else:
            self.trust_score = max(0, self.trust_score - 5)
