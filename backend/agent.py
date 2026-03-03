from llm import think
from planner import plan
from coder import code
from execution.executor import run_project

def nova(instruction, approve):
    raw = think(instruction)

    # 🔒 sanitize LLM/fallback noise
    if "LLM_ERROR" in raw or raw.strip() == "":
        plan_text = instruction
    else:
        plan_text = raw

    p = plan(plan_text)

    if not approve:
        return {
            "status": "PLAN_READY",
            "plan": p,
            "ask": True
        }

    path = code(p)
    result = run_project(path)

    return {
        "status": "LIVE",
        "path": path,
        "result": result
    }
