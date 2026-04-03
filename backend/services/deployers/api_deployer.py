from __future__ import annotations

from typing import Any


class APIDeployer:
    """
    Stub deployer for API publishing.
    """

    def deploy(self, output: dict[str, Any]) -> dict[str, Any]:
        return {
            "deployer": "api_deployer",
            "status": "stub",
            "message": "API deployment is not enabled in this environment.",
            "preview": self._preview(output),
        }

    @staticmethod
    def _preview(output: dict[str, Any]) -> str:
        return str(output)[:300]
