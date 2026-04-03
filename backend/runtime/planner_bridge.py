from backend.planner.planner import Planner


class PlannerBridge:

    def __init__(self):

        self.planner = Planner()

    # ---------------------------------
    # GENERATE PLAN
    # ---------------------------------

    def generate_plan(self, goal):

        plan = self.planner.build_plan(goal)

        return plan

    # ---------------------------------
    # EXECUTION ALLOWED
    # ---------------------------------

    def can_execute(self, plan):

        level = plan.get("autonomy_level")

        if level == "PLANNING_ONLY":
            return False

        if level == "HUMAN_APPROVAL_REQUIRED":
            return False

        return True