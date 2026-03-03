from typing import Dict, List


class PlannerConfidenceScorer:
    """
    Objective confidence scoring for planner output.
    Score range: 0 – 100

    This scorer does NOT execute anything.
    It only evaluates plan quality & risk.
    """

    def score(self, plan: Dict) -> int:
        score = 100
        penalties: List[int] = []

        # -----------------------------
        # 1. Mandatory structure checks
        # -----------------------------
        if not plan.get("goal"):
            penalties.append(30)

        if not plan.get("steps") or not isinstance(plan["steps"], list):
            penalties.append(25)

        if not plan.get("tools"):
            penalties.append(15)

        # -----------------------------
        # 2. Failure awareness
        # -----------------------------
        if not plan.get("assumed_failure"):
            penalties.append(20)

        if not plan.get("failure_impact"):
            penalties.append(15)

        # -----------------------------
        # 3. Plan complexity risk
        # -----------------------------
        steps_count = len(plan.get("steps", []))

        if steps_count == 0:
            penalties.append(40)
        elif steps_count > 10:
            penalties.append(15)
        elif steps_count > 5:
            penalties.append(8)

        # -----------------------------
        # 4. Tool risk
        # -----------------------------
        risky_tools = {"trade", "payment", "delete", "external_api"}

        tools = set(plan.get("tools", []))
        if tools & risky_tools:
            penalties.append(10)

        # -----------------------------
        # 5. Explicit human dependency
        # -----------------------------
        if plan.get("requires_human"):
            penalties.append(20)

        # -----------------------------
        # Final score calculation
        # -----------------------------
        total_penalty = sum(penalties)
        final_score = max(0, score - total_penalty)

        return final_score
