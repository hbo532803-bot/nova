from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.frontend_api.event_bus import broadcast


@dataclass(frozen=True)
class TaskNode:
    id: str
    name: str
    required_capabilities: list[str]
    actions: list[dict]
    depends_on: list[str]


class TaskGraphEngine:
    """
    Task graph (DAG) execution:
    - dependency relationships
    - parallel execution of ready nodes
    - intermediate outputs emitted into working memory / shared_context by Supervisor
    """

    def __init__(self, *, max_parallel: int = 3):
        self.max_parallel = max_parallel

    def parse(self, graph: Dict[str, Any]) -> List[TaskNode]:
        nodes = []
        for n in (graph.get("nodes") or []):
            nodes.append(
                TaskNode(
                    id=str(n.get("id")),
                    name=str(n.get("name") or n.get("id")),
                    required_capabilities=list(n.get("required_capabilities") or []),
                    actions=list(n.get("actions") or []),
                    depends_on=list(n.get("depends_on") or []),
                )
            )
        return nodes

    def run(
        self,
        graph: Dict[str, Any],
        *,
        run_node,  # callable(TaskNode) -> dict
    ) -> Dict[str, Any]:
        nodes = self.parse(graph)
        by_id = {n.id: n for n in nodes}

        # basic validation
        for n in nodes:
            for dep in n.depends_on:
                if dep not in by_id:
                    raise RuntimeError(f"TaskGraph invalid dependency: {n.id} depends_on {dep}")

        completed: Dict[str, Dict[str, Any]] = {}
        failed: Dict[str, str] = {}

        def is_ready(n: TaskNode) -> bool:
            return n.id not in completed and n.id not in failed and all(d in completed for d in n.depends_on)

        while len(completed) + len(failed) < len(nodes):
            ready = [n for n in nodes if is_ready(n)]
            if not ready:
                # deadlock (cycle) or upstream failures blocking progress
                remaining = [n.id for n in nodes if n.id not in completed and n.id not in failed]
                raise RuntimeError(f"TaskGraph deadlock_or_blocked remaining={remaining} failed={failed}")

            broadcast({"type": "log", "level": "info", "message": f"TaskGraph ready: {[n.id for n in ready]}"})

            # run batch in parallel
            batch = ready[: self.max_parallel]
            with ThreadPoolExecutor(max_workers=len(batch)) as ex:
                futs = {ex.submit(run_node, n): n for n in batch}
                for f in as_completed(futs):
                    n = futs[f]
                    try:
                        out = f.result()
                        completed[n.id] = out or {"ok": True}
                    except Exception as e:
                        failed[n.id] = str(e)
                        broadcast({"type": "log", "level": "error", "message": f"TaskGraph node failed {n.id}: {e}"})

        ok = not failed
        return {"ok": ok, "completed": completed, "failed": failed}

