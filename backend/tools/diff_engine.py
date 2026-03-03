from pathlib import Path
import difflib
import shutil
import time
from backend.frontend_api.event_bus import broadcast

# ---- GUARDRAILS ----
ALLOWED_PATHS = [
    "backend/",
]
MAX_DIFF_LINES = 300


def _allowed(path: str) -> bool:
    return any(path.startswith(p) for p in ALLOWED_PATHS)


def propose_change(path: str, new_content: str):
    if not _allowed(path):
        raise RuntimeError("PATH_NOT_ALLOWED")

    p = Path(path)
    old = p.read_text().splitlines(keepends=True)
    new = new_content.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        old, new,
        fromfile=path,
        tofile=f"{path} (proposed)"
    ))

    if len(diff) > MAX_DIFF_LINES:
        raise RuntimeError("DIFF_TOO_LARGE")

    broadcast({
        "type": "diff_proposal",
        "file": path,
        "diff": diff
    })

    return diff


def apply_change(path: str, new_content: str):
    if not _allowed(path):
        raise RuntimeError("PATH_NOT_ALLOWED")

    p = Path(path)

    # ---- BACKUP ----
    backup = f"{path}.bak.{int(time.time())}"
    shutil.copy(path, backup)

    p.write_text(new_content)

    broadcast({
        "type": "log",
        "level": "info",
        "message": f"Change applied. Backup: {backup}"
    })

    return {"applied": True, "backup": backup}
