import os
from backend.system.permission_gate import permission_gate

ALLOWED_READ_FOLDERS = {
    "backend/planner","backend/agents","backend/execution","system"
}

def _ok(path):
    n=os.path.normpath(path)
    return any(n.startswith(os.path.normpath(a)) for a in ALLOWED_READ_FOLDERS)

def read_file(path: str) -> str:
    if os.path.isdir(path): raise RuntimeError("Folder listing blocked")
    if not _ok(path):
        permission_gate.request("READ_FILE", path, "Analysis / review")
    with open(path,"r",encoding="utf-8") as f: return f.read()
