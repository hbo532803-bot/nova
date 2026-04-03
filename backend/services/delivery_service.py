from __future__ import annotations

from typing import Any

from backend.services.deployment_router import DeploymentRouter


class DeliveryService:
    """
    Maps aggregated task outputs into a user-facing final delivery object.
    """

    def __init__(self):
        self.deployment_router = DeploymentRouter()

    def build_final_result(
        self,
        aggregated: dict[str, Any],
        *,
        type_hint: str | None = None,
        deploy: bool = True,
    ) -> dict[str, Any]:
        task_outputs = aggregated.get("task_outputs") or []
        kind = self._detect_type(type_hint, task_outputs)

        final_result = {
            "type": kind,
            "status": "completed",
            "output": self._map_output(kind, task_outputs),
            "meta": {
                "mission_id": aggregated.get("mission_id"),
                "order_id": aggregated.get("order_id"),
                "task_count": len(task_outputs),
            },
        }
        if deploy:
            final_result["deployment"] = self.deployment_router.deploy(final_result)
        return final_result

    def _detect_type(self, type_hint: str | None, task_outputs: list[dict[str, Any]]) -> str:
        hint = (type_hint or "").lower()
        if "website" in hint:
            return "website"
        if "lead" in hint:
            return "leads"
        if "automation" in hint or "workflow" in hint:
            return "automation"

        blob = " ".join(str(item.get("output")) for item in task_outputs).lower()
        if "website" in blob or "landing" in blob:
            return "website"
        if "lead" in blob or "prospect" in blob:
            return "leads"
        if "automation" in blob or "workflow" in blob:
            return "automation"
        return "generic"

    def _map_output(self, kind: str, task_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        if kind == "website":
            return {
                "pages": self._extract_count(task_outputs, "page"),
                "artifacts": task_outputs,
            }
        if kind == "leads":
            return {
                "lead_items": self._extract_count(task_outputs, "lead"),
                "artifacts": task_outputs,
            }
        if kind == "automation":
            return {
                "workflows": self._extract_count(task_outputs, "workflow"),
                "artifacts": task_outputs,
            }
        return {"artifacts": task_outputs}

    @staticmethod
    def _extract_count(task_outputs: list[dict[str, Any]], token: str) -> int:
        token = token.lower()
        return sum(1 for item in task_outputs if token in str(item.get("output", "")).lower())
