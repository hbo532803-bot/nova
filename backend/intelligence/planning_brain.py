import json
import re

from backend.llm import think
from backend.frontend_api.event_bus import broadcast
from backend.intelligence.system_settings import get_setting


class PlanningBrain:

    """
    Nova Planning Brain

    Responsibilities
    ----------------
    • Convert goal → execution plan
    • Use LLM reasoning
    • Respect system reasoning depth
    """

    def generate_plan(self, goal: str):

        depth = int(get_setting("reasoning_depth", 1))

        broadcast({
            "type": "log",
            "level": "think",
            "message": f"Planning goal with depth {depth}"
        })

        prompt = f"""
You are Nova's strategic planning system.

Goal:
{goal}

Break this goal into an execution plan.

Reasoning depth: {depth}

Return JSON only.

Format:

{{
 "steps":[
  {{
   "id":1,
   "description":"..."
  }},
  {{
   "id":2,
   "description":"..."
  }}
 ]
}}
"""

        response = think(prompt)

        match = re.search(r"\{.*\}", response, re.DOTALL)

        if not match:

            broadcast({
                "type": "log",
                "level": "error",
                "message": "PlanningBrain failed to parse LLM output"
            })

            return {"error": "invalid_response"}

        try:

            plan = json.loads(match.group())

        except Exception:

            return {"error": "json_parse_failed"}

        broadcast({
            "type": "log",
            "level": "info",
            "message": "Plan generated successfully"
        })

        return plan

    # -------------------------------------------------
    # PLAN SUMMARY
    # -------------------------------------------------

    def summarize_plan(self, plan):

        steps = plan.get("steps", [])

        summary = [s["description"] for s in steps]

        return {
            "step_count": len(steps),
            "summary": summary
        }


# -------------------------------------------------
# GLOBAL INSTANCE (REQUIRED BY ROUTES)
# -------------------------------------------------

brain = PlanningBrain()