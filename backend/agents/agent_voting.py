from typing import List, Dict


class AgentVoting:
    """
    Resolves disagreement when multiple agents execute same plan.
    """

    def resolve(self, results: List[Dict]) -> Dict:
        """
        Strategy:
        - Prefer success
        - If multiple success → highest trust
        """
        successful = [r for r in results if r.get("success")]

        if not successful:
            return {
                "success": False,
                "reason": "All agents failed",
                "results": results
            }

        # choose highest trust
        chosen = sorted(
            successful,
            key=lambda r: r.get("agent_trust", 0),
            reverse=True
        )[0]

        return chosen
