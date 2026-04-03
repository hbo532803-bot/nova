from backend.database import get_db
from backend.runtime.agent_factory import AgentFactory


class AgentManager:

    def __init__(self):

        self.factory = AgentFactory()

    # --------------------------------------
    # GET OR CREATE AGENT
    # --------------------------------------

    def get_or_create_agent(self, name):

        agent = self.factory.find_agent_by_name(name)

        if agent:
            return agent["id"]

        return self.factory.create_agent(name)

    # --------------------------------------
    # HIBERNATE AGENT
    # --------------------------------------

    def hibernate_agent(self, agent_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            UPDATE agents
            SET status='HIBERNATED'
            WHERE id=?
            """, (agent_id,))

            conn.commit()

    # --------------------------------------
    # WAKE AGENT
    # --------------------------------------

    def wake_agent(self, agent_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            UPDATE agents
            SET status='ACTIVE'
            WHERE id=?
            """, (agent_id,))

            conn.commit()

    # --------------------------------------
    # UPDATE REVENUE
    # --------------------------------------

    def add_revenue(self, agent_id, revenue):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            UPDATE agents
            SET total_revenue = total_revenue + ?
            WHERE id=?
            """, (revenue, agent_id))

            conn.commit()

    # --------------------------------------
    # LIST AGENTS
    # --------------------------------------

    def list_agents(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT *
            FROM agents
            ORDER BY total_revenue DESC
            """)

            rows = cursor.fetchall()

        return rows