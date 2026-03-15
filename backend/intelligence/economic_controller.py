from datetime import datetime
from backend.database import get_db
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.roi_engine import ROIEngine


class EconomicController:

    LIFECYCLE = [
        "IDEA",
        "APPROVED",
        "TESTING",
        "LIVE",
        "SCALING",
        "FAILED",
        "ARCHIVED"
    ]

    def __init__(self):

        self.roi_engine = ROIEngine()
        self.confidence = ConfidenceEngine()

    # =========================================================
    # CORE ECONOMIC LOOP
    # =========================================================

    def run_full_cycle(self):

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, status
                FROM economic_experiments
                WHERE status NOT IN ('FAILED', 'ARCHIVED')
            """)

            experiments = cursor.fetchall()

        if not experiments:
            return {"status": "no_active_experiments"}

        results = []

        for exp in experiments:

            exp_id = exp["id"]

            roi_update = self.allocate_capital(exp_id)
            kill_result = self.auto_kill_if_needed(exp_id)
            lifecycle = self.evaluate_progress(exp_id)

            results.append({
                "experiment_id": exp_id,
                "roi_update": roi_update,
                "kill_check": kill_result,
                "lifecycle": lifecycle
            })

        return {
            "processed_experiments": len(results),
            "details": results
        }

    # =========================================================
    # LIFECYCLE LOGIC
    # =========================================================

    def evaluate_progress(self, experiment_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT status, validation_score, revenue_generated, iteration
                FROM economic_experiments
                WHERE id=?
            """, (experiment_id,))

            row = cursor.fetchone()

            if not row:
                return {"error": "Experiment not found"}

            status = row["status"]
            validation = row["validation_score"]
            revenue = row["revenue_generated"]
            iteration = row["iteration"]

            new_status = status

            if validation and validation >= 70 and status == "TESTING":
                new_status = "LIVE"

            if revenue and revenue >= 1000 and status == "LIVE":
                new_status = "SCALING"

            if validation is not None and validation < 30 and iteration > 2:
                new_status = "FAILED"

            if new_status != status:

                cursor.execute("""
                    UPDATE economic_experiments
                    SET status=?, last_tested=?
                    WHERE id=?
                """, (new_status, datetime.utcnow(), experiment_id))

                conn.commit()

                return {
                    "old_status": status,
                    "new_status": new_status
                }

        return {"status": "no_change"}

    # =========================================================
    # ROI + CAPITAL
    # =========================================================

    def allocate_capital(self, experiment_id):

        roi_result = self.roi_engine.update_roi(experiment_id)

        if not roi_result:
            return {"error": "ROI calculation failed"}

        roi = roi_result["roi"]

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT capital_allocated
                FROM economic_experiments
                WHERE id = ?
            """, (experiment_id,))

            row = cursor.fetchone()

            capital = row["capital_allocated"] if row else 0

            if capital == 0:
                capital = 100

            if roi > 0.2:
                capital *= 1.5
                self.confidence.adjust(+1)

            elif roi < 0:
                capital *= 0.5
                self.confidence.adjust(-1)

            cursor.execute("""
                UPDATE economic_experiments
                SET capital_allocated = ?
                WHERE id = ?
            """, (capital, experiment_id))

            conn.commit()

        return {
            "roi": roi,
            "new_capital": capital,
            "consecutive_losses": roi_result["consecutive_losses"]
        }

    # =========================================================
    # AUTO KILL
    # =========================================================

    def auto_kill_if_needed(self, experiment_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT consecutive_losses
                FROM economic_experiments
                WHERE id = ?
            """, (experiment_id,))

            row = cursor.fetchone()

            if not row:
                return None

            losses = row["consecutive_losses"]

            if losses >= 3:

                cursor.execute("""
                    UPDATE economic_experiments
                    SET status = 'FAILED'
                    WHERE id = ?
                """, (experiment_id,))

                conn.commit()

                self.confidence.adjust(-3)

                return {"status": "FAILED"}

        return {"status": "ACTIVE"}

    # =========================================================
    # REVENUE UPDATE
    # =========================================================

    def update_revenue(self, experiment_id, revenue):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE economic_experiments
                SET revenue_generated = revenue_generated + ?
                WHERE id=?
            """, (revenue, experiment_id))

            conn.commit()

        self.confidence.adjust(+2)

        return self.evaluate_progress(experiment_id)

    # =========================================================
    # VALIDATION UPDATE
    # =========================================================

    def update_validation(self, experiment_id, score):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE economic_experiments
                SET validation_score = ?, iteration = iteration + 1
                WHERE id=?
            """, (score, experiment_id))

            conn.commit()

        if score >= 60:
            self.confidence.adjust(+1)
        else:
            self.confidence.adjust(-2)

        return self.evaluate_progress(experiment_id)

    # =========================================================
    # AGENT REWARD
    # =========================================================

    def reward_agents(self, agent_name, revenue):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM agents WHERE name=?
            """, (agent_name,))

            row = cursor.fetchone()

            if not row:
                return {"error": "Agent not found"}

            agent_id = row["id"]

            trust_boost = min(10, int(revenue / 500))

            cursor.execute("""
                UPDATE agents
                SET total_revenue = total_revenue + ?
                WHERE id=?
            """, (revenue, agent_id))

            conn.commit()

        return {
            "agent_rewarded": agent_name,
            "boost": trust_boost
        }

    # =========================================================
    # MARKET → EXPERIMENT (CAPITAL SAFE)
    # =========================================================

    def create_experiment_from_market(self, niche_name, budget):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT total_capital, available_capital, reserved_capital
                FROM capital_pool
                WHERE id = 1
            """)

            capital_row = cursor.fetchone()

            if not capital_row:
                return {"error": "Capital pool not initialized"}

            total_capital = capital_row["total_capital"]
            available_capital = capital_row["available_capital"]
            reserved_capital = capital_row["reserved_capital"]

            max_allowed = available_capital * 0.6

            if budget > max_allowed:
                return {
                    "status": "rejected",
                    "reason": "Budget exceeds 60% exposure limit",
                    "max_allowed": round(max_allowed, 2)
                }

            if budget > available_capital:
                return {
                    "status": "rejected",
                    "reason": "Insufficient capital"
                }

            cursor.execute("""
                INSERT INTO economic_experiments
                (name, capital_allocated, status, iteration)
                VALUES (?, ?, 'APPROVED', 0)
            """, (niche_name, budget))

            new_available = available_capital - budget
            new_reserved = reserved_capital + budget

            cursor.execute("""
                UPDATE capital_pool
                SET available_capital = ?, reserved_capital = ?
                WHERE id = 1
            """, (new_available, new_reserved))

            conn.commit()

        return {
            "status": "approved",
            "experiment": niche_name,
            "allocated": budget,
            "remaining_capital": round(new_available, 2)
        }