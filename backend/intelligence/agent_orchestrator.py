import json
import re

from backend.llm import think
from backend.database import get_db
from backend.db_retry import run_db_write_with_retry

from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner
from backend.intelligence.economic_controller import EconomicController

from backend.frontend_api.event_bus import broadcast


class AgentOrchestrator:
    """
    Nova Agent Orchestrator

    Responsibilities
    ----------------
    • Coordinate AI agents
    • Run market intelligence cycle
    • Trigger economic engine
    • Store agent task history
    """

    def __init__(self):

        self.market_runner = MarketWeeklyRunner()
        self.economic_controller = EconomicController()

    # -------------------------------------------------
    # ENSURE AGENT TABLES
    # -------------------------------------------------

    def _ensure_tables(self):
        return None

    # -------------------------------------------------
    # REGISTER DEFAULT AGENTS
    # -------------------------------------------------

    def register_default_agents(self):

        self._ensure_tables()

        agents = [
            ("ResearchAgent", "Market Research", "Validate demand"),
            ("BuildAgent", "Product Builder", "Design architecture"),
            ("MarketingAgent", "Growth Planner", "Design acquisition"),
            ("FinanceAgent", "Monetization Planner", "Revenue model")
        ]

        with get_db() as conn:

            cursor = conn.cursor()

            for name, role, capability in agents:

                # The canonical agents schema uses the `name` column, created
                # in backend/db_init.initialize_all_tables. We keep role and
                # capability as conceptual attributes but only persist the
                # agent identity and lifecycle state here; detailed behavior is
                # tracked in agent_tasks.

                cursor.execute(
                    "SELECT id FROM agents WHERE name=?",
                    (name,)
                )

                if not cursor.fetchone():

                    cursor.execute("""
                    INSERT INTO agents (name, status)
                    VALUES (?, 'ACTIVE')
                    """, (name,))

            conn.commit()

    # -------------------------------------------------
    # EXECUTE AGENT TASK
    # -------------------------------------------------

    def execute_agent(self, agent_name, task):

        broadcast({
            "type": "log",
            "level": "think",
            "message": f"{agent_name} executing task"
        })

        prompt = f"""
You are {agent_name}.

Task:
{task}

Return JSON only.

{{
 "summary":"...",
 "key_points":["..."],
 "risks":["..."]
}}
"""

        response = think(prompt)

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            return {"error": "invalid_response"}

        try:
            result = json.loads(match.group())
        except Exception:
            return {"error": "json_parse_failed"}

        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_tasks (agent_name, task, result)
                VALUES (?, ?, ?)
                """,
                (agent_name, task, json.dumps(result)),
            )
            conn.commit()
            return None

        run_db_write_with_retry("agent_tasks.insert", _write)

        return result

    # -------------------------------------------------
    # ORCHESTRATE AGENT WORKFLOW
    # -------------------------------------------------

    def orchestrate(self, idea):

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Agent orchestration started"
        })

        self.register_default_agents()

        workflow = {
            "ResearchAgent": f"Validate market opportunity: {idea}",
            "BuildAgent": f"Design product architecture: {idea}",
            "MarketingAgent": f"Create launch strategy: {idea}",
            "FinanceAgent": f"Define monetization model: {idea}"
        }

        results = {}

        for agent, task in workflow.items():

            result = self.execute_agent(agent, task)

            results[agent] = result

        return {
            "idea": idea,
            "agent_results": results
        }

    # -------------------------------------------------
    # FULL SYSTEM CYCLE
    # -------------------------------------------------

    def run_full_system_cycle(self):

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Nova full system cycle started"
        })

        market_result = self.market_runner.run_full_weekly_cycle()

        economic_result = self.economic_controller.run_full_cycle()

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Nova system cycle completed"
        })

        return {
            "market_cycle": market_result,
            "economic_cycle": economic_result
        }
