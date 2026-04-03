import time
import datetime

from backend.system.kill_switch import kill_switch
from backend.system.permission_gate import permission_gate
from backend.budget_guard import check_budget

from backend.database import get_db

from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner

from backend.frontend_api.event_bus import broadcast


class NovaRuntime:

    def __init__(self):

        self.market_runner = MarketWeeklyRunner()

        self.last_market_run = None

        self.runtime_status = "IDLE"

    # -------------------------------------------------
    # CURRENT WEEK
    # -------------------------------------------------

    def _current_week(self):

        today = datetime.date.today()

        return f"{today.year}-W{today.isocalendar()[1]}"

    # -------------------------------------------------
    # SHOULD RUN MARKET ENGINE
    # -------------------------------------------------

    def should_run_market_cycle(self):

        current_week = self._current_week()

        if not self.last_market_run:
            return True

        if self.last_market_run != current_week:
            return True

        return False

    # -------------------------------------------------
    # RUN MARKET INTELLIGENCE
    # -------------------------------------------------

    def run_market_intelligence(self):

        try:

            broadcast({
                "type": "log",
                "level": "info",
                "message": "Starting weekly market intelligence cycle"
            })

            opportunities = self.market_runner.run_full_weekly_cycle()

            self.last_market_run = self._current_week()

            broadcast({
                "type": "log",
                "level": "info",
                "message": f"Market intelligence finished ({len(opportunities)} opportunities)"
            })

        except Exception as e:

            broadcast({
                "type": "log",
                "level": "error",
                "message": f"Market engine error: {str(e)}"
            })

    # -------------------------------------------------
    # FETCH MARKET PROPOSALS
    # -------------------------------------------------

    def fetch_market_proposals(self):

        week_tag = self._current_week()

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT id,
                       niche_name,
                       cash_score,
                       proposed_budget,
                       status
                FROM market_proposals
                WHERE week_tag = ?
                ORDER BY cash_score DESC
            """, (week_tag,))

            rows = cursor.fetchall()

        proposals = []

        for r in rows:

            proposals.append({
                "id": r["id"],
                "niche": r["niche_name"],
                "cash_score": r["cash_score"],
                "budget": r["proposed_budget"],
                "status": r["status"]
            })

        return proposals

    # -------------------------------------------------
    # PUSH PROPOSALS TO DASHBOARD
    # -------------------------------------------------

    def publish_proposals(self):

        proposals = self.fetch_market_proposals()

        broadcast({
            "type": "market_proposals",
            "data": proposals
        })

    # -------------------------------------------------
    # FETCH OWNER COMMANDS
    # -------------------------------------------------

    def fetch_commands(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, command_text, status
                FROM nova_commands
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
            """)

            rows = cursor.fetchall()

        return rows

    # -------------------------------------------------
    # PROCESS COMMANDS
    # -------------------------------------------------

    def process_commands(self):

        commands = self.fetch_commands()

        if not commands:
            return

        for cmd in commands:

            command_id = cmd["id"]

            command_text = cmd["command_text"]

            broadcast({
                "type": "log",
                "level": "info",
                "message": f"Processing command: {command_text}"
            })

            # ---------------------------
            # SAFETY CHECKS
            # ---------------------------

            if kill_switch.is_triggered():

                self._mark_command_failed(
                    command_id,
                    "Kill switch active"
                )

                continue

            if not check_budget():

                self._mark_command_failed(
                    command_id,
                    "Budget limit exceeded"
                )

                continue

            # ---------------------------
            # PERMISSION CHECK
            # ---------------------------

            if not permission_gate.is_allowed("command", command_text):

                self._mark_command_failed(
                    command_id,
                    "Permission denied"
                )

                continue

            # ---------------------------
            # COMMAND ACCEPTED
            # ---------------------------

            self._mark_command_running(command_id)

            broadcast({
                "type": "log",
                "level": "info",
                "message": f"Command accepted: {command_text}"
            })

            # Phase-1: execution placeholder
            # Agents will be connected in Phase-2

            time.sleep(1)

            self._mark_command_completed(command_id)

    # -------------------------------------------------
    # COMMAND STATE HELPERS
    # -------------------------------------------------

    def _mark_command_running(self, command_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE nova_commands
                SET status = 'RUNNING'
                WHERE id = ?
            """, (command_id,))

            conn.commit()

    def _mark_command_completed(self, command_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE nova_commands
                SET status = 'COMPLETED'
                WHERE id = ?
            """, (command_id,))

            conn.commit()

    def _mark_command_failed(self, command_id, reason):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE nova_commands
                SET status = 'FAILED'
                WHERE id = ?
            """, (command_id,))

            conn.commit()

        broadcast({
            "type": "log",
            "level": "error",
            "message": f"Command failed: {reason}"
        })

    # -------------------------------------------------
    # MAIN RUNTIME LOOP
    # -------------------------------------------------

    def start(self):

        self.runtime_status = "RUNNING"

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Nova runtime started"
        })

        while True:

            try:

                # ---------------------------------
                # MARKET INTELLIGENCE
                # ---------------------------------

                if self.should_run_market_cycle():

                    self.run_market_intelligence()

                # ---------------------------------
                # DASHBOARD UPDATE
                # ---------------------------------

                self.publish_proposals()

                # ---------------------------------
                # PROCESS OWNER COMMANDS
                # ---------------------------------

                self.process_commands()

                time.sleep(10)

            except Exception as e:

                broadcast({
                    "type": "log",
                    "level": "error",
                    "message": f"Runtime error: {str(e)}"
                })

                time.sleep(5)