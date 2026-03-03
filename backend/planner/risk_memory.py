from typing import List, Dict


class RiskMemory:
    """
    Extracts recurring risks from execution logs.
    """

    def extract_risks(self, logs: List[Dict]) -> List[str]:
        risks = set()

        for log in logs:
            if not log.get("success"):
                if log.get("assumed_failure"):
                    risks.add(log["assumed_failure"])

        return list(risks)
