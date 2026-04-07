import logging
import time
import uuid

from backend.runtime.planner_bridge import PlannerBridge
from backend.runtime.execution_router import ExecutionRouter
from backend.runtime.memory_bridge import MemoryBridge
from backend.runtime.system_monitor import SystemMonitor
from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner
from backend.frontend_api.event_bus import broadcast
from backend.system.audit_log import audit_log


class CognitiveLoop:

    def __init__(self):

        self.planner = PlannerBridge()
        self.executor = ExecutionRouter()
        self.memory = MemoryBridge()
        self.monitor = SystemMonitor()
        self.market = MarketWeeklyRunner()

    # -----------------------------------
    # RUN ONE CYCLE
    # -----------------------------------

    def run_cycle(self):

        cycle_id = str(uuid.uuid4())

        # -----------------------------------
        # 1. SYSTEM HEALTH
        # -----------------------------------

        self.monitor.broadcast_status()

        # -----------------------------------
        # 2. MARKET INTELLIGENCE
        # -----------------------------------

        try:
            self.market.run_full_weekly_cycle()
        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in cognitive_loop.py")

        # -----------------------------------
        # 3. FETCH PRIMARY GOAL
        # -----------------------------------

        goal = self.memory.current_goal()

        if not goal:
            broadcast({
                "type": "cognition",
                "message": "No active goal"
            })
            return

        # -----------------------------------
        # 4. BUILD PLAN
        # -----------------------------------

        plan = self.planner.generate_plan(goal)

        broadcast({
            "type": "plan",
            "data": plan
        })

        # -----------------------------------
        # 5. AUTONOMY CHECK
        # -----------------------------------

        if not self.planner.can_execute(plan):

            broadcast({
                "type": "autonomy",
                "message": "Execution blocked by autonomy policy"
            })

            return

        # -----------------------------------
        # 6. EXECUTE
        # -----------------------------------

        execution_result = self.executor.execute_command(goal)
        audit_log(
            actor="nova_loop",
            action="cognitive.execute",
            target=str(goal),
            payload={"reason": "planner_approved", "outcome": str(execution_result)},
        )

        # -----------------------------------
        # 7. REFLECT
        # -----------------------------------

        reflection_data = {
            "cycle_id": cycle_id,
            "primary_goal_snapshot": goal,
            "input_objective": goal,
            "execution_result": str(execution_result),
            "success": execution_result.get("status") == "EXECUTED",
            "confidence_before": plan.get("confidence_score"),
            "confidence_after": plan.get("confidence_score")
        }

        self.memory.record_result(reflection_data)

        broadcast({
            "type": "reflection",
            "data": reflection_data
        })

    # -----------------------------------
    # CONTINUOUS LOOP
    # -----------------------------------

    def start(self):

        broadcast({
            "type": "system",
            "message": "Nova cognitive loop started"
        })

        while True:

            try:
                self.run_cycle()
            except Exception as e:

                broadcast({
                    "type": "runtime_error",
                    "error": str(e)
                })

            time.sleep(30)
