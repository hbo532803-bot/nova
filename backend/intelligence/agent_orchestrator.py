import json
import re
from backend.llm import think
from backend.database import get_connection
from backend.intelligence.market_engine.weekly_runner import MarketWeeklyRunner
from backend.intelligence.economic_controller import EconomicController


class AgentOrchestrator:

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):
        self.market_runner = MarketWeeklyRunner()
        self.economic_controller = EconomicController()

    # =====================================================
    # ENSURE TABLES
    # =====================================================

    def _ensure_tables(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                role TEXT,
                capability TEXT,
                success_rate REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                task TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # =====================================================
    # REGISTER DEFAULT AGENTS
    # =====================================================

    def register_default_agents(self):

        self._ensure_tables()

        agents = [
            ("ResearchAgent", "Market Research", "Validate demand and competition"),
            ("BuildAgent", "Product Builder", "Design technical architecture"),
            ("MarketingAgent", "Growth Planner", "Design launch & acquisition strategy"),
            ("FinanceAgent", "Monetization Planner", "Design pricing & revenue model")
        ]

        conn = get_connection()
        cursor = conn.cursor()

        for name, role, capability in agents:
            cursor.execute("""
                SELECT id FROM agents WHERE agent_name = ?
            """, (name,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO agents (agent_name, role, capability)
                    VALUES (?, ?, ?)
                """, (name, role, capability))

        conn.commit()
        conn.close()

    # =====================================================
    # EXECUTE AGENT TASK
    # =====================================================

    def execute_agent(self, agent_name, task):

        prompt = f"""
You are {agent_name}.

Task:
{task}

Return only structured JSON:

{{
  "summary": "string",
  "key_points": ["point1", "point2"],
  "risks": ["risk1"]
}}
"""

        response = think(prompt)

        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            return {"error": "Invalid agent response"}

        try:
            result = json.loads(match.group())
        except:
            return {"error": "JSON parsing failed"}

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agent_tasks (agent_name, task, result)
            VALUES (?, ?, ?)
        """, (
            agent_name,
            task,
            json.dumps(result)
        ))

        conn.commit()
        conn.close()

        return result

    # =====================================================
    # AGENT WORKFLOW
    # =====================================================

    def orchestrate(self, idea):

        self.register_default_agents()

        workflow = {
            "ResearchAgent": f"Validate market for: {idea}",
            "BuildAgent": f"Design build plan for: {idea}",
            "MarketingAgent": f"Create launch strategy for: {idea}",
            "FinanceAgent": f"Create monetization model for: {idea}"
        }

        results = {}

        for agent, task in workflow.items():
            results[agent] = self.execute_agent(agent, task)

        return {
            "idea": idea,
            "agent_results": results
        }

    # =====================================================
    # FULL NOVA SYSTEM CYCLE
    # =====================================================

    def run_full_system_cycle(self):

        # 1️⃣ Market Scan
        market_result = self.market_runner.run_full_weekly_cycle()

        # 2️⃣ Economic Cycle
        economic_result = self.economic_controller.run_full_cycle()

        return {
            "market_cycle": market_result,
            "economic_cycle": economic_result
        }