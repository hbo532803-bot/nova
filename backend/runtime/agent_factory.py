from __future__ import annotations

import json
from typing import Any, Dict, List

from backend.database import get_db


class AgentFactory:

    def create_agent(self, name: str):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO agents (name, status)
            VALUES (?, 'ACTIVE')
            """, (name,))

            conn.commit()

            return cursor.lastrowid

    # ---------------------------------------
    # GET AGENT
    # ---------------------------------------

    def get_agent(self, agent_id):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT *
            FROM agents
            WHERE id=?
            """, (agent_id,))

            row = cursor.fetchone()

        return row

    # ---------------------------------------
    # FIND BY NAME
    # ---------------------------------------

    def find_agent_by_name(self, name):

        with get_db() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            SELECT *
            FROM agents
            WHERE name=?
            """, (name,))

            return cursor.fetchone()

    # ---------------------------------------
    # SPEC REGISTRY (system_settings)
    # ---------------------------------------

    def list_specs(self) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_settings WHERE key='agent_specs'")
            row = cursor.fetchone()
        if not row or not row["value"]:
            return []
        try:
            specs = json.loads(str(row["value"]))
            return specs if isinstance(specs, list) else []
        except Exception:
            return []

    def create_spec(self, *, required_capabilities: List[str], mission_id: str) -> Dict[str, Any]:
        """
        Generates a minimal agent spec to fill capability gaps.
        Stored in system_settings so AgentRegistry can load without file mutation.
        """
        caps = sorted({str(c) for c in (required_capabilities or []) if str(c).strip()})
        base = "AutoAgent"
        suffix = "_".join(caps[:2]) if caps else "General"
        name = f"{base}_{suffix}"

        spec = {
            "name": name,
            "capabilities": caps,
            "mission_id": str(mission_id or ""),
        }

        specs = self.list_specs()
        # de-dup by name
        if not any(s.get("name") == name for s in specs):
            specs.append(spec)

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", ("agent_specs", json.dumps(specs)))
            conn.commit()

        return {"ok": True, "spec": spec, "count": len(specs)}

    def evolve_specs(self) -> Dict[str, Any]:
        """
        Retire ineffective spec-agents based on handled_plan outcomes in agent_actions.
        A spec is retired if:
        - handled_plan events >= 5
        - success_rate < 0.3
        """
        specs = self.list_specs()
        if not specs:
            return {"ok": True, "retired": 0, "total": 0}

        stats: Dict[str, Dict[str, int]] = {}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT agent_name, result
                FROM agent_actions
                WHERE action='handled_plan'
                ORDER BY id DESC
                LIMIT 2000
                """
            )
            rows = cursor.fetchall()

        for r in rows:
            name = str(r["agent_name"])
            res = str(r["result"] or "")
            s = stats.setdefault(name, {"n": 0, "ok": 0})
            s["n"] += 1
            if res == "success":
                s["ok"] += 1

        retired = 0
        for s in specs:
            name = str(s.get("name") or "")
            st = stats.get(name) or {"n": 0, "ok": 0}
            n = int(st["n"])
            ok = int(st["ok"])
            if n >= 5:
                rate = ok / max(1, n)
                if rate < 0.3:
                    s["retired"] = True
                    retired += 1

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                ("agent_specs", json.dumps(specs)),
            )
            conn.commit()

        return {"ok": True, "retired": retired, "total": len(specs)}