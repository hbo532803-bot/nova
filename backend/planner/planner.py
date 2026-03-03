from planner.execution_log_reader import ExecutionLogReader
from planner.planner_confidence import PlannerConfidenceScorer
from planner.confidence_tuner import ConfidenceTuner
from planner.autonomy_manager import AutonomyManager
from planner.risk_memory import RiskMemory


class Planner:
    """
    Phase-2 Intelligent Planner
    """

    def __init__(self):
        self.log_reader = ExecutionLogReader()
        self.scorer = PlannerConfidenceScorer()
        self.tuner = ConfidenceTuner()
        self.autonomy = AutonomyManager()
        self.risk_memory = RiskMemory()

    def build_plan(self, goal: str) -> dict:
        # -----------------------------
        # 1. Base plan (existing logic)
        # -----------------------------
        plan = {
            "goal": goal,
            "steps": [
                "analyze",
                "prepare",
                "execute"
            ],
            "tools": ["external_api"],
            "assumed_failure": "API timeout or invalid response",
            "failure_impact": "Partial execution or inconsistent state",
        }

        # -----------------------------
        # 2. Base confidence
        # -----------------------------
        base_confidence = self.scorer.score(plan)

        # -----------------------------
        # 3. Read execution truth
        # -----------------------------
        logs = self.log_reader.read_all()

        # -----------------------------
        # 4. Tune confidence
        # -----------------------------
        tuned_confidence = self.tuner.tune(base_confidence, logs)
        plan["confidence_score"] = tuned_confidence

        # -----------------------------
        # 5. Autonomy decision
        # -----------------------------
        plan["autonomy_level"] = self.autonomy.autonomy_level(tuned_confidence)

        # -----------------------------
        # 6. Risk awareness injection
        # -----------------------------
        plan["known_risks"] = self.risk_memory.extract_risks(logs)

        return normalize_plan(plan)

# --- PATCH START (planner → agent contract normalizer) ---

def normalize_plan(plan: dict) -> dict:
    """
    Ensures planner output is agent-safe.
    Does NOT change planner logic.
    """

    # mandatory defaults
    plan.setdefault("steps", [])
    plan.setdefault("tools", [])
    plan.setdefault("assumed_failure", "unknown")
    plan.setdefault("failure_impact", "unknown")
    plan.setdefault("confidence_score", 0)
    plan.setdefault("autonomy_level", "PLANNING_ONLY")
    plan.setdefault("known_risks", [])

    # hard safety: no None values
    for k, v in list(plan.items()):
        if v is None:
            plan[k] = "unknown"

    return plan

# --- PATCH END ---
