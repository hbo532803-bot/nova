import subprocess
from backend.frontend_api.event_bus import broadcast

ALLOWED_COMMANDS = {
    "ls",
    "dir",
    "python --version"
}

def run_command(cmd: str, dry_run: bool = True):
    if cmd not in ALLOWED_COMMANDS:
        raise RuntimeError("COMMAND_NOT_ALLOWED")

    if dry_run:
        broadcast({
            "type": "log",
            "level": "info",
            "message": f"Dry-run approved: {cmd}"
        })
        return {"dry_run": True}

    result = subprocess.check_output(cmd, shell=True, text=True)

    broadcast({
        "type": "log",
        "level": "info",
        "message": f"Command output: {result[:200]}"
    })

    return {"output": result}
