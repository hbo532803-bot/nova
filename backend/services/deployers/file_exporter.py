from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class FileExporter:
    """
    Exports output payloads to CSV/JSON and returns saved file path.
    """

    def __init__(self, base_dir: str = "backend/memory/deployments/exports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def export(self, data: dict[str, Any], *, preferred_format: str = "json") -> dict[str, Any]:
        fmt = (preferred_format or "json").lower()
        if fmt == "csv":
            return self._to_csv(data)
        return self._to_json(data)

    def _to_json(self, data: dict[str, Any]) -> dict[str, Any]:
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        file_path = self.base_dir / f"result_{stamp}.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "deployer": "file_exporter",
            "status": "exported",
            "format": "json",
            "path": str(file_path),
        }

    def _to_csv(self, data: dict[str, Any]) -> dict[str, Any]:
        rows = self._flatten_rows(data)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        file_path = self.base_dir / f"result_{stamp}.csv"

        fields = sorted({k for row in rows for k in row.keys()}) or ["value"]
        with file_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        return {
            "deployer": "file_exporter",
            "status": "exported",
            "format": "csv",
            "path": str(file_path),
            "rows": len(rows),
        }

    @staticmethod
    def _flatten_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
        artifacts = data.get("artifacts") if isinstance(data, dict) else None
        if isinstance(artifacts, list) and artifacts:
            rows: list[dict[str, Any]] = []
            for item in artifacts:
                if isinstance(item, dict):
                    rows.append({k: str(v) for k, v in item.items()})
                else:
                    rows.append({"value": str(item)})
            return rows
        return [{"value": json.dumps(data, ensure_ascii=False)}]
