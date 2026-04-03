from __future__ import annotations

from typing import Any


class AutomationDeployer:
    """
    Stub deployer for automation workflows.
    """

    def deploy(self, output: dict[str, Any]) -> dict[str, Any]:
        return {
            "deployer": "automation_deployer",
            "status": "stub",
            "message": "Automation deployment is not enabled in this environment.",
            "preview": self._preview(output),
        }

    @staticmethod
    def _preview(output: dict[str, Any]) -> str:
        return str(output)[:300]
