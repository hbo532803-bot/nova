import logging
import json
from datetime import datetime
from backend.database import get_db
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.roi_engine import ROIEngine
from backend.intelligence.metrics_engine import MetricsEngine
from backend.intelligence.metric_decision_engine import MetricDecisionEngine
from backend.intelligence.profit_intelligence_engine import ProfitIntelligenceEngine
from backend.intelligence.revenue_execution_engine import RevenueExecutionEngine


class EconomicController:

    LIFECYCLE = [
        "IDEA",
        "APPROVED",
        "TESTING",
        "LIVE",
        "PAUSED",
        "SCALING",
        "FAILED",
        "ARCHIVED"
    ]

    def __init__(self):

        self.roi_engine = ROIEngine()
        self.confidence = ConfidenceEngine()
        self.metrics_engine = MetricsEngine()
        self.metric_decider = MetricDecisionEngine()
        self.profit_engine = ProfitIntelligenceEngine()
        self.execution_engine = RevenueExecutionEngine()

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
            priority_update = self.profit_engine.update_priority(exp_id)
            hard_stop = self.enforce_hard_stop_rules(exp_id)
            kill_result = self.auto_kill_if_needed(exp_id)
            lifecycle = self.evaluate_progress(exp_id)
            metric_decision = self.apply_metric_decision(exp_id)
            execution_plan = self.execution_engine.execute_for_experiment(
                int(exp_id),
                priority_level=str((priority_update or {}).get("priority_level") or "LOW"),
                decision=str((metric_decision or {}).get("decision") or "hold"),
            )
            execution_result = self.execution_engine.run_pending_actions(experiment_id=int(exp_id))

            results.append({
                "experiment_id": exp_id,
                "roi_update": roi_update,
                "priority_update": priority_update,
                "hard_stop": hard_stop,
                "kill_check": kill_result,
                "lifecycle": lifecycle,
                "metric_decision": metric_decision,
                "execution_plan": execution_plan,
                "execution_result": execution_result,
            })

        comparison = self.profit_engine.compare_experiments(limit=max(20, len(results)))

        return {
            "processed_experiments": len(results),
            "details": results,
            "comparison": comparison,
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
        priority = self.profit_engine.update_priority(experiment_id)

        with get_db() as conn:

            cursor = conn.cursor()
            cursor.execute("SELECT total_capital FROM capital_pool WHERE id=1")
            pool = cursor.fetchone()
            total_capital = float((pool["total_capital"] or 0.0) if pool else 0.0)
            cap_limit = max(100.0, total_capital * 0.25)

            cursor.execute("""
                SELECT capital_allocated, cost_real_total
                FROM economic_experiments
                WHERE id = ?
            """, (experiment_id,))

            row = cursor.fetchone()

            capital = row["capital_allocated"] if row else 0
            used = float((row["cost_real_total"] or 0.0) if row else 0.0)

            if capital == 0:
                capital = 100

            level = str(priority.get("priority_level") or "LOW")
            if roi > 0 and level == "HIGH":
                capital *= 1.5
                self.confidence.adjust(+1)
            elif roi > 0 and level == "MEDIUM":
                capital *= 1.15
            elif roi < 0 or level == "LOW":
                capital *= 0.5
                self.confidence.adjust(-1)
            capital = min(capital, cap_limit)
            capital_remaining = max(0.0, capital - used)

            cursor.execute("""
                UPDATE economic_experiments
                SET capital_allocated = ?, capital_used=?, capital_remaining=?, capital_cap=?
                WHERE id = ?
            """, (capital, used, capital_remaining, cap_limit, experiment_id))

            conn.commit()

        return {
            "roi": roi,
            "priority_level": priority.get("priority_level"),
            "new_capital": capital,
            "capital_used": used,
            "capital_remaining": capital_remaining,
            "capital_cap": cap_limit,
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
    # METRIC-DRIVEN DECISION
    # =========================================================

    def apply_metric_decision(self, experiment_id):

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, status, name FROM economic_experiments WHERE id=?", (experiment_id,))
            row = cursor.fetchone()

        if not row:
            return {"error": "experiment_not_found"}

        metrics = self.metrics_engine.compute(experiment_id=int(experiment_id))
        decision = self.metric_decider.decide(metrics)
        economics = self.profit_engine.update_profit_snapshot(experiment_id)
        current_status = str(row["status"] or "")
        next_status = current_status

        reliable = bool((economics.get("reliability") or {}).get("is_data_reliable"))
        has_real_revenue = float((economics.get("revenue_components") or {}).get("real_payment") or 0.0) > 0
        if decision["decision"] == "scale" and float(economics.get("roi") or 0.0) > 0 and reliable and has_real_revenue:
            next_status = "SCALING"
        elif decision["decision"] == "scale":
            decision = {"decision": "hold", "reason": "requires_reliable_real_payment_revenue"}
        elif decision["decision"] == "fail":
            next_status = "FAILED"
        elif decision["decision"] == "optimize" and current_status in {"LIVE", "SCALING"}:
            next_status = "TESTING"
        elif decision["decision"] == "gather_more_data":
            next_status = current_status

        with get_db() as conn:
            cursor = conn.cursor()
            if next_status != current_status:
                cursor.execute(
                    "UPDATE economic_experiments SET status=?, last_tested=? WHERE id=?",
                    (next_status, datetime.utcnow(), experiment_id),
                )

            cursor.execute(
                """
                INSERT INTO experiment_feedback_loops (experiment_id, strategy_key, metrics_json, decision, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    int(experiment_id),
                    str(row["name"] or "strategy_unknown"),
                    json.dumps(metrics),
                    str(decision["decision"]),
                    str(decision["reason"]),
                ),
            )
            conn.commit()

        return {
            "decision": decision["decision"],
            "reason": decision["reason"],
            "status_before": current_status,
            "status_after": next_status,
            "metrics": metrics.get("metrics", {}),
            "economics": {
                "profit": economics.get("profit"),
                "roi": economics.get("roi"),
                "revenue_source": economics.get("revenue_source"),
                "priority": self.profit_engine.update_priority(experiment_id).get("priority_level"),
            },
        }

    def enforce_hard_stop_rules(self, experiment_id):
        economics = self.profit_engine.update_profit_snapshot(int(experiment_id))
        reliable = bool((economics.get("reliability") or {}).get("is_data_reliable"))
        roi = float(economics.get("roi") or 0.0)
        trend = economics.get("time_windows") or {}
        cost_without_conversion = bool(trend.get("cost_increasing_without_conversion"))

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM economic_experiments WHERE id=?", (int(experiment_id),))
            row = cursor.fetchone()
            if not row:
                return {"status": "unknown"}
            current = str(row["status"] or "")

            if reliable and roi < 0:
                cursor.execute("UPDATE economic_experiments SET status='FAILED', last_tested=? WHERE id=?", (datetime.utcnow(), int(experiment_id)))
                conn.commit()
                return {"status": "STOP", "reason": "negative_roi_with_reliable_sample", "from": current, "to": "FAILED"}

            if cost_without_conversion and current not in {"FAILED", "ARCHIVED"}:
                cursor.execute("UPDATE economic_experiments SET status='PAUSED', last_tested=? WHERE id=?", (datetime.utcnow(), int(experiment_id)))
                conn.commit()
                return {"status": "PAUSE", "reason": "cost_increasing_without_conversion_improvement", "from": current, "to": "PAUSED"}

        return {"status": "NO_ACTION"}

    # =========================================================
    # REVENUE UPDATE
    # =========================================================

    def track_experiment_cost(self, experiment_id, amount, *, source="manual_input", is_simulated=False):

        tracked = self.profit_engine.track_cost(
            int(experiment_id),
            float(amount),
            source=str(source),
            is_simulated=bool(is_simulated),
        )
        economics = self.profit_engine.update_profit_snapshot(int(experiment_id))
        return {"tracked": tracked, "economics": economics}

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

    def create_experiment_from_market(self, niche_name, budget, *, conn=None):
        """
        If conn is provided, runs inside caller transaction.
        """
        owned = conn is None
        if owned:
            with get_db() as _conn:
                return self.create_experiment_from_market(niche_name, budget, conn=_conn)

        try:
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

            if owned:
                conn.commit()

            return {
            "status": "approved",
            "experiment": niche_name,
            "allocated": budget,
            "remaining_capital": round(new_available, 2)
            }
        except Exception:
            if owned:
                try:
                    conn.rollback()
                except Exception:
                    logging.getLogger(__name__).exception("Suppressed exception in economic_controller.py")
            raise
        finally:
            if owned:
                try:
                    conn.close()
                except Exception:
                    logging.getLogger(__name__).exception("Suppressed exception in economic_controller.py")
