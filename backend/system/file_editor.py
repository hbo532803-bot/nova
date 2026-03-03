from backend.system.permission_gate import permission_gate

def propose_edit(path: str, diff: str):
    permission_gate.request("EDIT_FILE", path, "Propose diff (no auto-apply)")
    return {"path": path, "diff": diff}
