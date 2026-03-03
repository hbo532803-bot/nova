from backend.frontend_api.event_bus import broadcast
from backend.memory.reflection_memory import ReflectionMemory
from backend.intelligence.confidence_engine import ConfidenceEngine


class PlanExecutor:

    def execute_plan(self, goal: str, plan: dict):

        reflection = ReflectionMemory()

        for step in plan.get("steps", []):

            broadcast({
                "type": "log",
                "level": "think",
                "message": f"Executing step {step['id']}: {step['description']}"
            })

            # Simulated execution
            success = True

            reflection.record_reflection({
                "cycle_id": f"{goal}-{step['id']}",
                "primary_goal_snapshot": goal,
                "input_objective": step["description"],
                "execution_result": "Completed",
                "success": success,
                "confidence_before": ConfidenceEngine.score,
                "confidence_after": ConfidenceEngine.score
            })

            if success:
                ConfidenceEngine.success()
            else:
                ConfidenceEngine.failure()

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Strategic plan execution completed"
        })
