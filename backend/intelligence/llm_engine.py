import json
from backend.database import get_db
from backend.llm import think
from backend.intelligence.system_settings import get_setting


def run_llm_reasoning(input_data: dict):

    goal = input_data.get("goal")

    if not goal:
        return {"error": "No goal provided"}

    semantic_threshold = float(get_setting("semantic_threshold", 0.75))
    reasoning_depth = int(get_setting("reasoning_depth", 1))
    recursive_planning = get_setting("recursive_planning", "disabled")

    system_prompt = f"""
You are a strategic planning AI.

Goal: {goal}

Reasoning depth: {reasoning_depth}
Recursive planning: {recursive_planning}
Semantic threshold: {semantic_threshold}

Return STRICT JSON:

{{
 "steps":[
   {{"id":1,"description":"step description"}}
 ]
}}
"""

    raw_response = think(system_prompt)

    try:

        parsed = json.loads(raw_response)

        steps = parsed.get("steps", [])

        if recursive_planning == "enabled" and reasoning_depth > 1:

            expanded = []

            for step in steps:
                expanded.append(step)
                expanded.append({
                    "id": step["id"] * 10,
                    "description": f"Sub-task of {step['description']}"
                })

            steps = expanded

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO plan_memory (goal, plan_json) VALUES (?,?)",
                (goal, json.dumps(steps))
            )

            conn.commit()

        return {
            "status": "completed",
            "steps": steps
        }

    except Exception as e:

        return {
            "error": "LLM parsing failed",
            "details": str(e),
            "raw": raw_response
        }