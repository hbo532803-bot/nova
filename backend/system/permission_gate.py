from backend.frontend_api.event_bus import broadcast

class PermissionGate:
    """
    Strict, ordered, one-time permission gate.
    No permission implies any other.
    """

    def __init__(self):
        # allowed_once[(action, target)] = True
        self.allowed_once = {}

        # permission dependency chain
        self.PREREQUISITES = {
            "CHANGE_FILE": ["READ_FILE"],
            "DELETE_FILE": ["READ_FILE"],
        }

    # ------------------------
    # Internal helpers
    # ------------------------

    def _key(self, action: str, target: str):
        return (action, target)

    def is_allowed(self, action: str, target: str) -> bool:
        return self.allowed_once.get(self._key(action, target), False)

    # ------------------------
    # Public API
    # ------------------------

    def request(self, action: str, target: str, reason: str):
        """
        Ask for permission.
        Raises RuntimeError if permission or prerequisite missing.
        """

        # 1️⃣ check prerequisites FIRST
        prereqs = self.PREREQUISITES.get(action, [])
        for prereq in prereqs:
            if not self.is_allowed(prereq, target):
                broadcast({
                    "type": "permission_request",
                    "action": prereq,
                    "target": target,
                    "reason": f"Required before {action}"
                })
                raise RuntimeError(f"PREREQ_REQUIRED:{prereq}")

        # 2️⃣ check actual permission
        if not self.is_allowed(action, target):
            broadcast({
                "type": "permission_request",
                "action": action,
                "target": target,
                "reason": reason
            })
            raise RuntimeError("PERMISSION_REQUIRED")

        # allowed
        return True

    def allow_once(self, action: str, target: str):
        """
        Allow a permission exactly once.
        """
        self.allowed_once[self._key(action, target)] = True

    def reset(self):
        """
        Clear all permissions (safety).
        """
        self.allowed_once.clear()


# 🔒 singleton
permission_gate = PermissionGate()
