from pathlib import Path
import shutil
from backend.frontend_api.event_bus import broadcast

BACKUP_GLOB = "*.bak.*"
MAX_KEEP = 10

def list_backups(path: str):
    p = Path(path)
    backups = sorted(p.parent.glob(p.name + ".bak.*"), key=lambda x: x.stat().st_mtime, reverse=True)
    return [str(b) for b in backups[:MAX_KEEP]]

def rollback_last(path: str):
    backups = list_backups(path)
    if not backups:
        raise RuntimeError("NO_BACKUP_AVAILABLE")

    latest = Path(backups[0])
    target = Path(path)
    shutil.copy(latest, target)

    broadcast({
        "type": "log",
        "level": "warn",
        "message": f"Rollback applied from {latest.name}"
    })
    return {"rolled_back_from": latest.name}
