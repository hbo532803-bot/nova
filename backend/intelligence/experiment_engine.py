import json
import re
from backend.llm import think
from backend.database import get_db
from backend.db_retry import run_db_write_with_retry


class EconomicEngine:

    # -------------------------
    # Generate Experiments
    # -------------------------
    def generate_experiments(self):

        prompt = """
You are an autonomous AI economic strategist.

Generate exactly 5 small money-making experiments.

Constraints:
- Solo builder possible
- AI automation friendly
- Low initial cost
- Scalable potential

Return ONLY valid JSON.
No explanation.
No markdown.
No text outside JSON.

Format:

{
  "experiments": [
    {
      "idea": "string",
      "model_type": "service/startup/tool",
      "automation_level": 1,
      "build_time_days": 1,
      "cost_level": "low",
      "scalability": 1,
      "risk": 1
    }
  ]
}
"""

        response = think(prompt)

        print("RAW ECONOMIC RESPONSE:")
        print(response)

        # Extract JSON safely
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            print("No JSON found in response.")
            return []

        try:
            parsed = json.loads(match.group())
            experiments = parsed.get("experiments", [])
            return experiments
        except Exception as e:
            print("JSON parse failed:", e)
            return []

    # -------------------------
    # Score Experiment
    # -------------------------
    def score_experiment(self, exp):

        score = 0

        score += exp.get("automation_level", 0) * 2
        score += exp.get("scalability", 0) * 2
        score -= exp.get("risk", 0)

        if exp.get("cost_level") == "low":
            score += 5

        if exp.get("build_time_days", 10) <= 5:
            score += 5

        return score

    # -------------------------
    # Select Best
    # -------------------------
    def select_best(self, experiments):

        if not experiments:
            return None

        best = None
        best_score = -999

        for exp in experiments:
            s = self.score_experiment(exp)
            exp["internal_score"] = s

            if s > best_score:
                best_score = s
                best = exp

        return best

    # -------------------------
    # Store in DB
    # -------------------------
    def store_experiment(self, experiment):
      name = str(experiment.get("idea") or "")
      exp_type = str(experiment.get("model_type") or "")
      score = int(experiment.get("internal_score") or 0)

      def _write(conn):
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO economic_experiments (name, experiment_type, notes, status, iteration)
            VALUES (?, ?, ?, 'IDEA', 0)
            """,
            (name, exp_type, f"legacy_internal_score={score}"),
        )
        conn.commit()
        return None

      run_db_write_with_retry("economic_experiments.insert.legacy", _write)

    # -------------------------
    # Run Full Cycle
    # -------------------------
    def run_cycle(self):

        experiments = self.generate_experiments()

        if not experiments:
            return {"error": "No experiments generated"}

        best = self.select_best(experiments)

        if not best:
            return {"error": "Scoring failed"}

        self.store_experiment(best)

        return {
            "selected_experiment": best,
            "all_experiments": experiments
        }
