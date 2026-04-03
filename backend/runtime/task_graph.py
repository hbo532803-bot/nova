class TaskGraph:

    def build_experiment_graph(self, niche, experiment_id):

        graph = [

            {
                "agent": "research_agent",
                "task": f"research market for {niche}",
                "experiment_id": experiment_id
            },

            {
                "agent": "backend_dev_agent",
                "task": f"build backend prototype for {niche}",
                "experiment_id": experiment_id
            },

            {
                "agent": "frontend_dev_agent",
                "task": f"create frontend demo for {niche}",
                "experiment_id": experiment_id
            },

            {
                "agent": "testing_agent",
                "task": f"test system for {niche}",
                "experiment_id": experiment_id
            },

            {
                "agent": "deployment_agent",
                "task": f"deploy prototype for {niche}",
                "experiment_id": experiment_id
            }

        ]

        return graph