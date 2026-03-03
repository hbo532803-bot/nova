import json
import re
from backend.llm import think
from backend.database import get_connection


class BlueprintEngine:

    # ----------------------------
    # Generate Blueprint
    # ----------------------------
    def generate_blueprint(self, experiment):

        prompt = f"""
You are a strategic startup execution planner.

Create a full execution blueprint for this idea:

Idea: {experiment.get("idea")}
Model Type: {experiment.get("model_type")}

Return ONLY valid JSON.
No explanation.
No markdown.

Format:

{{
  "idea": "string",
  "tech_stack": ["tool1", "tool2"],
  "automation_strategy": "string",
  "monetization_model": "string",
  "launch_steps": ["step1", "step2"],
  "seven_day_plan": ["day1", "day2"]
}}
"""

        response = think(prompt)

        print("RAW BLUEPRINT RESPONSE:")
        print(response)

        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            return None

        try:
            parsed = json.loads(match.group())
            return parsed
        except Exception as e:
            print("Blueprint JSON parse error:", e)
            return None

    # ----------------------------
    # Store Blueprint
    # ----------------------------
    def store_blueprint(self, blueprint):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_blueprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idea TEXT,
                blueprint_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT INTO execution_blueprints (idea, blueprint_json)
            VALUES (?, ?)
        """, (
            blueprint.get("idea"),
            json.dumps(blueprint)
        ))

        conn.commit()
        conn.close()

    # ----------------------------
    # Run Full Cycle
    # ----------------------------
    def run_cycle(self):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT idea, model_type, internal_score
            FROM economic_experiments
            ORDER BY id DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"error": "No experiment found"}

        experiment = {
            "idea": row["idea"],
            "model_type": row["model_type"],
            "internal_score": row["internal_score"]
        }

        blueprint = self.generate_blueprint(experiment)

        if not blueprint:
            return {"error": "Blueprint generation failed"}

        self.store_blueprint(blueprint)

        return {
            "experiment": experiment,
            "blueprint": blueprint
        }
