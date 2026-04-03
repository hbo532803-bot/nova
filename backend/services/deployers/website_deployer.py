from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


class WebsiteDeployer:
    """
    Minimal website deployer: persists HTML locally and returns file URL/path.
    """

    def __init__(self, base_dir: str = "backend/memory/deployments/websites"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def deploy(self, output: dict[str, Any]) -> dict[str, Any]:
        html = self._extract_html(output)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        file_path = self.base_dir / f"website_{stamp}.html"
        file_path.write_text(html, encoding="utf-8")

        return {
            "deployer": "website_deployer",
            "status": "deployed",
            "target": "local_file",
            "path": str(file_path),
            "url": file_path.resolve().as_uri(),
        }

    @staticmethod
    def _extract_html(output: dict[str, Any]) -> str:
        candidate = output.get("html") if isinstance(output, dict) else None
        if isinstance(candidate, str) and candidate.strip():
            return candidate

        title = "Nova Website Output"
        body = "<p>Generated website artifact.</p>"
        return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body>{body}</body></html>"
