from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class CapabilityProfile:
    agent_name: str
    capabilities: set[str]


class CapabilityRegistry:
    """
    Structured capability registry and scoring.
    Supervisor/Registry can use this to match tasks to agents via capability scoring.
    """

    def score(self, agent_caps: set[str], required: Iterable[str]) -> float:
        req = set(required)
        if not req:
            return 0.0
        overlap = agent_caps & req
        return len(overlap) / max(1, len(req))

    def best(self, profiles: List[CapabilityProfile], required: Iterable[str]) -> List[Tuple[CapabilityProfile, float]]:
        scored = [(p, self.score(p.capabilities, required)) for p in profiles]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

