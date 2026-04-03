from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.frontend_api.event_bus import broadcast
from backend.memory.working_memory import WorkingMemoryStore


@dataclass
class TeamTask:
    name: str
    required_capabilities: list[str]
    actions: list[dict]


class CollaborationOrchestrator:
    """
    Orchestrates multi-step tasks via agent teams:
    - task decomposition
    - role assignment (via required_capabilities)
    - intermediate result sharing (shared_context)

    Agents never execute system actions; they propose decisions and write intermediate
    results to shared_context.
    """

    def decompose(self, plan: Dict[str, Any]) -> List[TeamTask]:
        actions = plan.get("actions") or []
        tasks: List[TeamTask] = []

        for idx, act in enumerate(actions):
            at = str(act.get("type", "")).upper()
            caps = []
            if "OPPORTUNITY" in at or "MARKET" in at:
                caps = ["research", "opportunity_discovery", "product_research"]
            elif "EXPERIMENT" in at:
                caps = ["growth_experimentation", "marketing", "traffic", "engagement", "conversions", "finance", "portfolio"]
            elif "AGENT_" in at:
                caps = ["agent_ops"]
            else:
                caps = list(plan.get("required_capabilities") or [])

            tasks.append(TeamTask(name=f"{at}[{idx}]", required_capabilities=caps, actions=[act]))

        return tasks

    def share(self, shared_context: Dict[str, Any], key: str, value: Any, *, mission_id: Optional[str] = None) -> None:
        shared_context[key] = value
        try:
            if mission_id:
                WorkingMemoryStore().put(mission_id, key, str(value))
        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in collaboration.py")
        broadcast({"type": "log", "level": "info", "message": f"Shared context updated: {key}"})

