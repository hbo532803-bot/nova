from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from typing import Any, Dict, List

from backend.frontend_api.event_bus import broadcast

# Strict allowlist: base command -> allowed first-arg variants (best-effort).
_ALLOW: dict[str, set[str] | None] = {
    "echo": None,
    "git": {"status"},
}


def _parse(command: str) -> List[str]:
    try:
        return shlex.split(command, posix=False)
    except Exception:
        # Fallback: split on whitespace
        return [p for p in command.split() if p]


def safe_execute(command: str) -> Dict[str, Any]:
    """
    Safe SHELL execution:
    - shell=False (no injection)
    - strict allowlist
    - sandboxed working directory
    - structured stdout/stderr capture
    """
    parts = _parse(command)
    if not parts:
        return {"ok": False, "blocked": True, "reason": "empty_command"}

    base = str(parts[0]).lower()
    allowed_args = _ALLOW.get(base)
    if allowed_args is None:
        allowed = base in _ALLOW
    else:
        allowed = len(parts) >= 2 and str(parts[1]).lower() in allowed_args

    if not allowed:
        broadcast({"type": "log", "level": "warn", "message": f"Blocked unsafe command: {command}"})
        return {"ok": False, "blocked": True, "reason": "command_not_allowlisted", "command": command}

    # Best-effort sandbox directory; no repo writes by default.
    with tempfile.TemporaryDirectory(prefix="nova_shell_") as tmp:
        try:
            res = subprocess.run(
                parts,
                shell=False,
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=10,
                env={"PATH": os.environ.get("PATH", "")},
            )
            out = {
                "ok": res.returncode == 0,
                "returncode": int(res.returncode),
                "stdout": (res.stdout or "")[:8000],
                "stderr": (res.stderr or "")[:8000],
                "command": parts,
                "cwd": tmp,
            }
            broadcast(
                {
                    "type": "log",
                    "level": "info" if out["ok"] else "warn",
                    "message": f"shell: rc={out['returncode']}",
                }
            )
            return out
        except Exception as e:
            broadcast({"type": "log", "level": "warn", "message": str(e)})
            return {"ok": False, "error": str(e), "command": parts}
