import json
import re

from backend.llm import think
from backend.database import get_db


class BlueprintEngine:

    def generate_blueprint(self, experiment):

        idea = experiment.get("idea")
        model = experiment.get("model_type")
        score = experiment.get("internal_score")

        prompt = f"""
You are Nova's product architecture system.

Design a complete technical blueprint for launching a startup.

IDEA:
{idea}

BUSINESS MODEL:
{model}

INTERNAL SCORE:
{score}

Return JSON only.

Format:

{{
 "idea": "...",
 "product_type": "...",

 "core_features":[
   "...",
   "...",
   "..."
 ],

 "technical_architecture":{{
   "backend":"...",
   "frontend":"...",
   "database":"...",
   "apis":["..."]
 }},

 "mvp_scope":[
   "...",
   "..."
 ],

 "monetization":"...",
 "launch_strategy":"..."
}}
"""

        response = think(prompt)

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:
            return None

        try:
            return json.loads(match.group())
        except Exception:
            return None

    def store_blueprint(self, blueprint):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO execution_blueprints
            (idea, blueprint_json)
            VALUES (?,?)
            """, (
                blueprint.get("idea"),
                json.dumps(blueprint)
            ))

            conn.commit()

    def run_cycle(self):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT idea, model_type, internal_score
            FROM economic_experiments
            ORDER BY id DESC
            LIMIT 1
            """)

            row = cursor.fetchone()

        if not row:
            return {"error": "no_experiment"}

        experiment = dict(row)

        blueprint = self.generate_blueprint(experiment)

        if not blueprint:
            return {"error": "generation_failed"}

        self.store_blueprint(blueprint)

        return blueprint