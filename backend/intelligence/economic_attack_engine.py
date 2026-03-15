from backend.database import get_db
from backend.intelligence.economic_controller import EconomicController
from backend.intelligence.roi_engine import ROIEngine
from backend.intelligence.confidence_engine import ConfidenceEngine

from backend.guards.cost_guard import CostGuard
from backend.system.permission_gate import PermissionGate
from backend.guards.circuit_breaker import CircuitBreaker

from backend.frontend_api.event_bus import broadcast


class EconomicAttackEngine:

    MAX_CONCURRENT_EXPERIMENTS = 5
    MAX_CAPITAL_EXPOSURE = 0.5
    ROI_SCALE_THRESHOLD = 0.5
    MAX_CONSECUTIVE_LOSSES = 3

    def __init__(self):

        self.controller = EconomicController()
        self.roi_engine = ROIEngine()
        self.confidence = ConfidenceEngine()

        self.cost_guard = CostGuard(max_budget=500)
        self.permission_gate = PermissionGate()
        self.circuit_breaker = CircuitBreaker()

    # -------------------------------------------------
    # MAIN ECONOMIC CYCLE
    # -------------------------------------------------

    def run_cycle(self):

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Economic engine cycle started"
        })

        proposals = self.load_proposals()
        filtered = self.filter_proposals(proposals)
        launched = self.launch_experiments(filtered)
        managed = self.manage_experiments()
        scaled = self.scale_profitable()
        killed = self.kill_bad_experiments()

        return {
            "launched": launched,
            "managed": managed,
            "scaled": scaled,
            "killed": killed
        }

    # -------------------------------------------------
    # LOAD MARKET PROPOSALS
    # -------------------------------------------------

    def load_proposals(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, niche_name, proposed_budget, cash_score
            FROM market_proposals
            WHERE status='PENDING'
            ORDER BY cash_score DESC
            """)

            rows = cursor.fetchall()

        return rows

    # -------------------------------------------------
    # FILTER PROPOSALS
    # -------------------------------------------------

    def filter_proposals(self, proposals):

        safe = []

        for p in proposals:

            budget = p["proposed_budget"]

            if not self.cost_guard.check_budget(budget):
                continue

            safe.append(p)

        return safe

    # -------------------------------------------------
    # ACTIVE EXPERIMENT COUNT
    # -------------------------------------------------

    def active_experiment_count(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT COUNT(*)
            FROM economic_experiments
            WHERE status NOT IN ('FAILED','ARCHIVED')
            """)

            count = cursor.fetchone()[0]

        return count

    # -------------------------------------------------
    # CAPITAL CHECK
    # -------------------------------------------------

    def capital_state(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT available_capital, total_capital
            FROM capital_pool
            WHERE id=1
            """)

            row = cursor.fetchone()

        return row

    # -------------------------------------------------
    # LAUNCH EXPERIMENTS
    # -------------------------------------------------

    def launch_experiments(self, proposals):

        launched = []

        active = self.active_experiment_count()
        capital = self.capital_state()

        if not capital:
            return []

        available = capital["available_capital"]
        total = capital["total_capital"]

        if available / total < (1 - self.MAX_CAPITAL_EXPOSURE):
            return []

        with get_db() as conn:

            cursor = conn.cursor()

            for p in proposals:

                if active >= self.MAX_CONCURRENT_EXPERIMENTS:
                    break

                niche = p["niche_name"]
                budget = p["proposed_budget"]
                pid = p["id"]

                if not self.permission_gate.allow("economic_experiment"):
                    break

                if self.circuit_breaker.tripped():
                    break

                if budget > available:
                    continue

                available -= budget

                result = self.controller.create_experiment_from_market(
                    niche_name=niche,
                    budget=budget
                )

                if result.get("status") == "approved":

                    cursor.execute("""
                    UPDATE market_proposals
                    SET status='LAUNCHED'
                    WHERE id=?
                    """, (pid,))

                    launched.append(niche)

                    active += 1

            conn.commit()

        return launched

    # -------------------------------------------------
    # MANAGE EXPERIMENTS
    # -------------------------------------------------

    def manage_experiments(self):

        return self.controller.run_full_cycle()

    # -------------------------------------------------
    # SCALE PROFITABLE
    # -------------------------------------------------

    def scale_profitable(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, roi, capital_allocated
            FROM economic_experiments
            WHERE status='SCALING'
            """)

            rows = cursor.fetchall()

            scaled = []

            for row in rows:

                exp_id = row["id"]

                roi = self.roi_engine.calculate_roi(exp_id)

                if roi and roi > self.ROI_SCALE_THRESHOLD:

                    current_capital = row["capital_allocated"]

                    new_capital = current_capital * 1.5
                    added_capital = new_capital - current_capital

                    cursor.execute("""
                    UPDATE economic_experiments
                    SET capital_allocated = ?
                    WHERE id=?
                    """, (new_capital, exp_id))

                    cursor.execute("""
                    UPDATE capital_pool
                    SET reserved_capital = reserved_capital + ?
                    WHERE id=1
                    """, (added_capital,))

                    scaled.append(exp_id)

                    self.confidence.adjust(+2)

            conn.commit()

        return scaled

    # -------------------------------------------------
    # KILL BAD EXPERIMENTS
    # -------------------------------------------------

    def kill_bad_experiments(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT id, consecutive_losses, capital_allocated
            FROM economic_experiments
            WHERE status NOT IN ('FAILED','ARCHIVED')
            """)

            rows = cursor.fetchall()

            killed = []

            for r in rows:

                exp_id = r["id"]
                losses = r["consecutive_losses"]
                capital = r["capital_allocated"]

                if losses >= self.MAX_CONSECUTIVE_LOSSES:

                    cursor.execute("""
                    UPDATE economic_experiments
                    SET status='FAILED'
                    WHERE id=?
                    """, (exp_id,))

                    cursor.execute("""
                    UPDATE capital_pool
                    SET reserved_capital = reserved_capital - ?
                    WHERE id=1
                    """, (capital,))

                    killed.append(exp_id)

                    self.confidence.adjust(-2)

            conn.commit()

        return killed