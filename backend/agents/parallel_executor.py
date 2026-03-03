from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelAgentExecutor:
    """
    Executes multiple agents in parallel (read-only / low-risk).
    """

    def execute(self, agents: List, plan: Dict) -> List[Dict]:
        results = []

        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {
                executor.submit(agent.execute, plan): agent
                for agent in agents
            }

            for future in as_completed(futures):
                agent = futures[future]
                try:
                    output = future.result()
                    output["agent_trust"] = agent.trust_score
                    results.append(output)
                except Exception as exc:
                    results.append({
                        "agent": agent.name,
                        "success": False,
                        "error": str(exc),
                        "agent_trust": agent.trust_score
                    })

        return results
