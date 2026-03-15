from backend.intelligence.economic_controller import EconomicController
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.roi_engine import ROIEngine
from backend.intelligence.agent_orchestrator import AgentOrchestrator
from backend.intelligence.system_settings import get_setting
from backend.budget_guard import check_budget
from backend.system.permission_gate import permission_gate
from backend.system.kill_switch import kill_switch
from backend.database import get_db


class Nova:

    def __init__(self):

        self.economic = EconomicController()
        self.confidence = ConfidenceEngine()
        self.roi_engine = ROIEngine()

    # =========================================================
    # -------------------- STATUS DASHBOARD -------------------
    # =========================================================

    def status(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM economic_experiments")
            total = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT SUM(revenue_generated) as revenue
                FROM economic_experiments
            """)
            revenue_row = cursor.fetchone()
            revenue = revenue_row["revenue"] if revenue_row["revenue"] else 0

            cursor.execute("""
                SELECT SUM(cost_incurred) as cost
                FROM economic_experiments
            """)
            cost_row = cursor.fetchone()
            cost = cost_row["cost"] if cost_row["cost"] else 0

        confidence_state = self.confidence.get_state()

        return {
            "experiments": total,
            "total_revenue": revenue,
            "total_cost": cost,
            "net_profit": revenue - cost,
            "confidence": confidence_state
        }

    # =========================================================
    # -------------------- MAIN ECONOMIC LOOP -----------------
    # =========================================================

    def run_cycle(self):

        if kill_switch.is_triggered():
            return {"status": "SYSTEM_HALTED"}

        if not check_budget():
            return {"status": "BUDGET_EXCEEDED"}

        result = self.economic.run_full_cycle()

        return {
            "status": "CYCLE_COMPLETED",
            "details": result
        }

    # =========================================================
    # -------------------- EXPERIMENT CONTROL -----------------
    # =========================================================

    def run_experiment(self):
        return self.economic.run_full_cycle()

    def update_revenue(self, experiment_id: int, revenue: float):
        return self.economic.update_revenue(experiment_id, revenue)

    def update_validation(self, experiment_id: int, score: float):
        return self.economic.update_validation(experiment_id, score)

    # =========================================================
    # -------------------- APPROVAL GATE ----------------------
    # =========================================================

    def approve_action(self, action: str, target: str):

        permission_gate.allow_once(action, target)

        return {"approved": True}

    # =========================================================
    # -------------------- EMERGENCY CONTROL ------------------
    # =========================================================

    def emergency_stop(self):

        kill_switch.trigger()

        return {"status": "EMERGENCY_STOP_ACTIVATED"}

    def reset_emergency(self):

        kill_switch.reset()

        return {"status": "SYSTEM_RESUMED"}