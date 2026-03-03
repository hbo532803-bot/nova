from typing import Dict, Any
import time
import json
import os
import uuid

from backend.memory.reflection_memory import ReflectionMemory
from backend.memory.goal_memory import primary_goal


class ExecutionFeedbackRecorder:
    """
    Records execution outcomes for planner learning.
    NO hidden memory.
    ONLY explicit log files.
    """

    def __init__(self, log_dir: str = "logs/execution"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def record(
        self,
        plan: Dict[str, Any],
        result: Dict[str, Any],
    ) -> None:
        """
        Called AFTER execution finishes (success or failure)
        """

        # ----------------------------
        # ORIGINAL EXECUTION FEEDBACK
        # ----------------------------

        feedback = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "goal": plan.get("goal"),
            "confidence_score": plan.get("confidence_score"),
            "assumed_failure": plan.get("assumed_failure"),
            "failure_impact": plan.get("failure_impact"),

            # execution outcome
            "success": result.get("success"),
            "error": result.get("error"),
            "rolled_back": result.get("rolled_back"),
            "duration_ms": result.get("duration_ms"),

            # meta
            "steps_count": len(plan.get("steps", [])),
            "tools": plan.get("tools", []),
        }

        filename = self._build_filename(plan)
        path = os.path.join(self.log_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(feedback, f, indent=2)

        # ----------------------------
        # DIGITAL ORGANISM REFLECTION
        # ----------------------------

        try:
            reflection = ReflectionMemory()

            success_flag = result.get("success")

            confidence_before = plan.get("confidence_score")
            confidence_after = result.get("confidence_score", confidence_before)

            confidence_delta = (
                confidence_after - confidence_before
                if confidence_before is not None and confidence_after is not None
                else 0
            )

            reflection.record_reflection({
                "cycle_id": str(uuid.uuid4()),
                "primary_goal_snapshot": primary_goal(),
                "input_objective": plan.get("goal"),
                "refined_intent": plan.get("goal"),
                "plan_summary": f"{len(plan.get('steps', []))} steps",
                "execution_result": "success" if success_flag else result.get("error"),
                "success": success_flag,

                "reasoning_depth_score": len(plan.get("steps", [])),
                "alignment_score": 90 if success_flag else 60,
                "complexity_score": len(plan.get("steps", [])),
                "risk_score": 20 if success_flag else 70,

                "assumptions_made": [],
                "assumptions_invalidated": [],

                "decision_quality": "high" if success_flag else "failure",
                "mistake_type": "" if success_flag else "execution_error",
                "missed_simplification": "",

                "confidence_before": confidence_before,
                "confidence_after": confidence_after,
                "confidence_delta": confidence_delta,

                "system_stress_level": "normal",
                "architecture_limitation_detected": False,
                "limitation_details": "",

                "meta_reasoner_override": False,
                "admin_intervention": False,

                "improvement_suggestions": [],
                "pattern_tags": []
            })

        except Exception as e:
            # Reflection must NEVER break execution
            print("Reflection logging failed:", e)

    def _build_filename(self, plan: Dict[str, Any]) -> str:
        safe_goal = (plan.get("goal") or "unknown").replace(" ", "_")[:40]
        ts = int(time.time())
        return f"{safe_goal}_{ts}.json"
