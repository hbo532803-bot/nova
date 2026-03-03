from backend.system.permission_gate import permission_gate

SAFE = {"ls","pwd","python"}

def run_command(cmd: str):
    base = cmd.split()[0]
    if base not in SAFE: raise RuntimeError("Command blocked")
    permission_gate.request("RUN_COMMAND", cmd, "Dev-safe command")
    return {"dry_run": True, "cmd": cmd}
