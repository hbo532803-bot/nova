import subprocess
from backend.frontend_api.event_bus import broadcast

ALLOWED_COMMANDS = [
    "dir",
    "ls",
    "echo",
    "git status"
]

def safe_execute(command: str):
    base = command.split(" ")[0]

    if base not in ALLOWED_COMMANDS:
        broadcast({
            "type": "log",
            "level": "warn",
            "message": f"Blocked unsafe command: {command}"
        })
        return {"blocked": True}

    try:
        result = subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.STDOUT,
            timeout=10
        ).decode()

        broadcast({
            "type": "log",
            "level": "info",
            "message": result
        })

        return {"ok": True}

    except Exception as e:
        broadcast({
            "type": "log",
            "level": "warn",
            "message": str(e)
        })
        return {"error": True}
