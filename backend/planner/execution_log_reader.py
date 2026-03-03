import os
import json
from typing import List, Dict


class ExecutionLogReader:
    """
    Reads execution feedback logs.
    Explicit memory only (files).
    """

    def __init__(self, log_dir: str = "logs/execution"):
        self.log_dir = log_dir

    def read_all(self) -> List[Dict]:
        if not os.path.exists(self.log_dir):
            return []

        logs = []
        for file in os.listdir(self.log_dir):
            if not file.endswith(".json"):
                continue

            path = os.path.join(self.log_dir, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    logs.append(json.load(f))
            except Exception:
                continue

        return logs
