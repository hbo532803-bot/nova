import datetime

from backend.core.nova_core import nova_core
from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.intelligence.economic_attack_engine import EconomicAttackEngine
from backend.frontend_api.event_bus import broadcast
from backend.database import get_db
from backend.intelligence.self_improvement_engine import SelfImprovementEngine

class NovaBrainLoop:
    """
    Central autonomous loop of Nova.

    Responsibilities:
    - Observe system state
    - Decide strategic action
    - Execute via NovaCore
    - Run economic engine
    - Learn from results
    """

    def __init__(self):

        self.confidence = ConfidenceEngine()
        self.economic_engine = EconomicAttackEngine()
        self.self_improvement = SelfImprovementEngine()

    # -------------------------------------------------
    # MAIN CYCLE
    # -------------------------------------------------

    def run_cycle(self):

        state = self.confidence.get_state()
        learning = self.self_improvement.run_cycle()

        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Nova brain cycle started (confidence={state['score']})"
        })

        # -------------------------------
        # 1️⃣ Observe system
        # -------------------------------

        observation = self._observe()

        # -------------------------------
        # 2️⃣ Decide strategy
        # -------------------------------

        action = self._decide_action(state, observation)

        broadcast({
            "type": "log",
            "level": "think",
            "message": f"Nova decision: {action}"
        })

        # -------------------------------
        # 3️⃣ Execute via NovaCore
        # -------------------------------

        strategy_result = nova_core.handle_command(action)

        # -------------------------------
        # 4️⃣ Run economic engine
        # -------------------------------

        economic_result = self.economic_engine.run_cycle()

        # -------------------------------
        # 5️⃣ Learning
        # -------------------------------

        self._learn(strategy_result)

        return {
            "strategy": strategy_result,
            "economy": economic_result,
            "strategy": strategy_result,
            "economy": economic_result,
             "learning": learning

        }

    # -------------------------------------------------
    # SYSTEM OBSERVATION
    # -------------------------------------------------

    def _observe(self):

        with get_db() as conn:
         cursor = conn.cursor()

        cursor.execute("""
        SELECT COUNT(*) AS total
        FROM economic_experiments
        WHERE status NOT IN ('FAILED','ARCHIVED')
        """)

        active_experiments = cursor.fetchone()["total"]

        cursor.execute("""
        SELECT COUNT(*) AS pending
        FROM market_proposals
        WHERE status='PENDING'
        """)

        pending_proposals = cursor.fetchone()["pending"]

        conn.close()

        return {
            "active_experiments": active_experiments,
            "pending_proposals": pending_proposals
        }

    # -------------------------------------------------
    # DECISION ENGINE
    # -------------------------------------------------

    def _decide_action(self, state, observation):

        confidence = state["score"]

        active_exp = observation["active_experiments"]

        pending_prop = observation["pending_proposals"]

        # System stabilization
        if confidence < 60:
            return "analyze system"

        # Generate more market intelligence
        if pending_prop < 3:
            return "analyze market"

        # Expand experiments
        if confidence > 80 and active_exp < 3:
            return "expand experiments"

        # Default
        return "optimize strategy"

    # -------------------------------------------------
    # LEARNING SYSTEM
    # -------------------------------------------------

    def _learn(self, result):

        try:

            if result.get("success"):

                self.confidence.adjust(+1)

            else:

                self.confidence.adjust(-1)

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "warn",
                "message": f"Learning update failed: {e}"
            })