"""
LLM Router:
- fast model for UI/text
- smart model for planning/refactor
- budget guard
- safe degrade
"""
class Budget:
    def __init__(self, limit=50.0):
        self.limit=limit; self.used=0.0
    def charge(self,c):
        if self.used+c>self.limit: raise RuntimeError("LLM_BUDGET_EXCEEDED")
        self.used+=c

budget = Budget()

def fast_llm(prompt:str)->str:
    budget.charge(0.1)
    return "FAST_OK"

def smart_llm(prompt:str)->str:
    budget.charge(0.5)
    return "SMART_OK"

def ask(task:str, prompt:str)->str:
    try:
        if task in {"ui","status","summary"}:
            return fast_llm(prompt)
        return smart_llm(prompt)
    except:
        return "LLM_DEGRADED_RESPONSE"
