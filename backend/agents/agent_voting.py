from backend.frontend_api.event_bus import broadcast


class AgentVotingSystem:

    """
    Nova Agent Voting System

    Combines:
    - agent score
    - agent trust
    - vote weight

    Agents submit decisions
    System evaluates weighted score
    Best action is selected
    """

    WEIGHTS = {
        "analysis": 0.30,
        "strategy": 0.40,
        "risk": 0.20,
        "execution": 0.10
    }

    SCORE_WEIGHT = 0.7
    TRUST_WEIGHT = 0.3

    # --------------------------------------
    # COLLECT VOTES
    # --------------------------------------

    def collect_votes(self, agent_outputs):

        votes = []

        for agent, output in agent_outputs.items():

            votes.append({
                "agent": agent,
                "decision": output.get("decision"),
                "score": output.get("score", 0),
                "type": output.get("type")
            })

        return votes

    # --------------------------------------
    # COMPUTE WEIGHTED SCORE
    # --------------------------------------

    def compute_scores(self, votes):

        scored = []

        for v in votes:

            weight = self.WEIGHTS.get(v["type"], 0.1)

            final_score = v["score"] * weight

            scored.append({
                "decision": v["decision"],
                "score": final_score
            })

        return scored

    # --------------------------------------
    # SELECT BEST DECISION
    # --------------------------------------



    def resolve(self, results):

        if not results:
            raise RuntimeError("No agent results")

        scored = []

        for r in results:

            decision = r.get("decision")
            score = r.get("score", 0)
            trust = r.get("agent_trust", 1)
            agent = r.get("agent")

            vote_type = r.get("type", "execution")

            weight = self.WEIGHTS.get(vote_type, 0.1)

            weighted = (
                score * weight * self.SCORE_WEIGHT +
                trust * self.TRUST_WEIGHT
            )

            scored.append({
                "decision": decision,
                "agent": agent,
                "score": weighted
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        best = scored[0]

        broadcast({
            "type": "log",
            "level": "think",
            "message": f"Voting selected {best}"
        })

        return {
            "decision": best["decision"],
            "agent": best["agent"],
            "score": best["score"],
            "success": True
        }

    def select_best(self, scored):

        if not scored:
            return None

        scored.sort(key=lambda x: x["score"], reverse=True)

        best = scored[0]

        broadcast({
            "type": "log",
            "level": "think",
            "message": f"Agent decision selected: {best}"
        })

        return best["decision"]

    # --------------------------------------
    # MAIN ENTRY
    # --------------------------------------

    def vote(self, agent_outputs):

        votes = self.collect_votes(agent_outputs)

        scored = self.compute_scores(votes)

        decision = self.select_best(scored)

        return decision