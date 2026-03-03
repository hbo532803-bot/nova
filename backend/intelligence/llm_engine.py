import json
from backend.database import get_connection
from backend.llm import think
from backend.intelligence.system_settings import get_setting


def run_llm_reasoning(input_data: dict):

    goal = input_data.get("goal")

    if not goal:
        return {"error": "No goal provided"}

    # ---------------- LOAD EVOLUTION SETTINGS ----------------
    semantic_threshold = float(get_setting("semantic_threshold", 0.75))
    reasoning_depth = int(get_setting("reasoning_depth", 1))
    recursive_planning = get_setting("recursive_planning", "disabled")

    print("LLM CALLED")
    print("CONFIG:", semantic_threshold, reasoning_depth, recursive_planning)

    # ---------------- BUILD PROMPT ----------------
    system_prompt = f"""
You are a strategic planning AI.

Goal: {goal}

Reasoning depth: {reasoning_depth}
Recursive planning: {recursive_planning}
Semantic threshold: {semantic_threshold}

Return STRICT JSON:

{{
    "steps": [
        {{"id": 1, "description": "step description"}}
    ]
}}
"""

    raw_response = think(system_prompt)

    print("RAW LLM RESPONSE:", raw_response)

    try:
        parsed = json.loads(raw_response)

        steps = parsed.get("steps", [])

        if recursive_planning == "enabled" and reasoning_depth > 1:
            # Simple expansion logic
            expanded_steps = []
            for step in steps:
                expanded_steps.append(step)
                expanded_steps.append({
                    "id": step["id"] * 10,
                    "description": f"Sub-task of: {step['description']}"
                })
            steps = expanded_steps

        # Store plan in DB
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO plan_memory (goal, plan_json) VALUES (?, ?)",
            (goal, json.dumps(steps))
        )

        conn.commit()
        conn.close()

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
