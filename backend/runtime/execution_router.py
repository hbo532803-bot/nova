from backend.runtime.strategy_engine import StrategyEngine
from backend.runtime.agent_manager import AgentManager
from backend.runtime.task_graph import TaskGraph
from backend.runtime.agent_tasks import AgentTaskRunner


class ExecutionRouter:

    def __init__(self):

        self.strategy = StrategyEngine()
        self.agents = AgentManager()
        self.task_runner = AgentTaskRunner()

    # ---------------------------------
    # EXECUTE COMMAND
    # ---------------------------------

    def execute_command(self, command_text):

        command_text = command_text.lower()

        if "experiment" in command_text or "build" in command_text:

            proposals = self.strategy.fetch_pending_proposals()

            if not proposals:
                return {"status": "NO_PROPOSALS"}

            proposal = proposals[0]

            experiment_id = self.strategy.create_experiment(proposal)

            task_graph = TaskGraph().build_experiment_graph(
                proposal["niche"],
                experiment_id
            )

            results = []

            for task in task_graph:

                agent_id = self.agents.get_or_create_agent(task["agent"])

                self.agents.wake_agent(agent_id)

                result = self.task_runner.run_task(agent_id, task)

                results.append(result)

                self.agents.hibernate_agent(agent_id)

            return {
                "status": "EXECUTED",
                "tasks": len(results)
            }

        return {"status": "UNKNOWN_COMMAND"}