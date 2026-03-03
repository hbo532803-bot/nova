import json
import re
from backend.llm import think
from backend.database import get_db
from backend.frontend_api.event_bus import broadcast


class StrategicPlanner:

    # ==========================================
    # MAIN ENTRY — DECOMPOSE GOAL
    # ==========================================

    def decompose_goal(self, goal: str):

        # --------------------------------------
        # 1️⃣ CHECK IF PLAN ALREADY EXISTS
        # --------------------------------------

        existing_plan = self.load_latest_plan(goal)
        if existing_plan:
            broadcast({
                "type": "log",
                "level": "info",
                "message": "Reusing existing plan from memory"
            })
            return existing_plan

        broadcast({
            "type": "log",
            "level": "think",
            "message": "Strategic Planner: Decomposing goal"
        })

        # --------------------------------------
        # 2️⃣ BUILD PROMPT
        # --------------------------------------

        prompt = f"""
You are a strategic planning engine.

Break the following goal into clear structured execution steps.

Rules:
- Respond ONLY in valid JSON.
- No explanation.
- No markdown.
- No extra text.

Format strictly like:

{{
    "steps": [
        {{"id": 1, "description": "..."}},
        {{"id": 2, "description": "..."}}
    ]
}}

Goal:
{goal}
"""

        # --------------------------------------
        # 3️⃣ CALL LLM
        # --------------------------------------

        response = think(prompt)

        # --------------------------------------
        # 4️⃣ EXTRACT JSON
        # --------------------------------------

        plan = self._extract_json(response)

        # Retry once if failed
        if not plan:
            broadcast({
                "type": "log",
                "level": "warn",
                "message": "Planner retrying JSON extraction"
            })

            retry_prompt = prompt + "\nReturn strictly valid JSON."
            retry_response = think(retry_prompt)
            plan = self._extract_json(retry_response)

        # --------------------------------------
        # 5️⃣ SAFE FALLBACK
        # --------------------------------------

        if not plan:
            broadcast({
                "type": "log",
                "level": "warn",
                "message": "Planner fallback activated"
            })

            plan = {
                "steps": [
                    {"id": 1, "description": goal}
                ]
            }

        # --------------------------------------
        # 6️⃣ STORE PLAN
        # --------------------------------------

        self.store_plan(goal, plan)

        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Plan created with {len(plan.get('steps', []))} steps"
        })

        return plan


    # ==========================================
    # SAFE JSON EXTRACTION
    # ==========================================

    def _extract_json(self, text: str):

        if not text:
            return None

        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return None

        try:
            parsed = json.loads(match.group())
            if "steps" in parsed and isinstance(parsed["steps"], list):
                return parsed
        except Exception:
            return None

        return None


    # ==========================================
    # STORE PLAN IN DB
    # ==========================================

    def store_plan(self, goal: str, plan: dict):

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO plan_memory (goal, plan_json, status)
                VALUES (?, ?, ?)
            """, (
                goal,
                json.dumps(plan),
                "CREATED"
            ))

            conn.commit()


    # ==========================================
    # LOAD LATEST PLAN
    # ==========================================

    def load_latest_plan(self, goal: str):

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT plan_json
                FROM plan_memory
                WHERE goal = ?
                ORDER BY id DESC
                LIMIT 1
            """, (goal,))

            row = cursor.fetchone()

        if row:
            try:
                return json.loads(row[0])
            except Exception:
                return None

        return None
