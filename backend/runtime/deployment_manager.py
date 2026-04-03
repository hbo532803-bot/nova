from backend.frontend_api.event_bus import broadcast


class DeploymentManager:

    def validate_before_deploy(self, result):

        if not result:
            return False

        if "error" in str(result).lower():
            return False

        return True

    def deploy(self, artifact):

        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Deploying artifact: {artifact}"
        })

        return {"deployed": True}