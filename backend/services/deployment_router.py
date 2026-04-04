from __future__ import annotations

from typing import Any

from backend.services.deployers.website_deployer import WebsiteDeployer
from backend.services.deployers.file_exporter import FileExporter
from backend.services.deployers.api_deployer import APIDeployer
from backend.services.deployers.automation_deployer import AutomationDeployer


class DeploymentRouter:
    """
    Routes delivery outputs to deployers by result type.
    """

    def __init__(self):
        self.website = WebsiteDeployer()
        self.file_exporter = FileExporter()
        self.api = APIDeployer()
        self.automation = AutomationDeployer()

    def deploy(self, result: dict[str, Any]) -> dict[str, Any]:
        result_type = str(result.get("type") or "generic").lower()
        output = result.get("output") or {}
        mission_id = str((result.get("meta") or {}).get("mission_id") or "")

        if result_type == "website":
            return self.website.deploy(output, mission_id=mission_id)

        if result_type == "leads":
            return self.file_exporter.export(output, preferred_format="csv")

        if result_type == "automation":
            return self.automation.deploy(output)

        if result_type == "api":
            return self.api.deploy(output)

        return self.file_exporter.export(output, preferred_format="json")
