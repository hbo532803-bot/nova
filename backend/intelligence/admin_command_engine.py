from __future__ import annotations

import json
from typing import Any, Dict, List

from backend.database import get_db
from backend.execution.action_types import ActionType
from backend.system.audit_log import audit_log


class AdminCommandEngine:
    """Natural-language admin command parser + mission queue creator."""

    def parse_command(self, *, command_text: str, admin_user: str = "admin") -> Dict[str, Any]:
        cmd = str(command_text or "").strip()
        lower = cmd.lower()

        mission_type = "general"
        category = "lead_generation"
        required_capabilities: List[str] = ["analysis"]
        actions: List[Dict[str, Any]] = []

        if any(x in lower for x in ["linkedin", "x", "twitter", "reddit", "fiverr", "upwork"]):
            mission_type = "market_discovery"
            required_capabilities = ["research", "opportunity_discovery"]
            actions.append(
                {
                    "type": ActionType.MARKET_INTELLIGENCE_SCAN.value,
                    "payload": {"query": cmd, "real_only": True, "limit": 25},
                    "assumed_failure": "market_intelligence_scan_fails",
                    "failure_impact": "opportunities_not_discovered",
                }
            )

        if "website" in lower:
            category = "website_development"
        elif any(x in lower for x in ["automation", "workflow", "crm"]):
            category = "automation"
        elif any(x in lower for x in ["lead", "outreach", "inbound"]):
            category = "lead_generation"

        if mission_type == "general":
            mission_type = "execution"
            required_capabilities = ["analysis", "growth_experimentation", "execution"]
            actions.append(
                {
                    "type": ActionType.EXECUTION_APPLY_PRIORITY.value,
                    "payload": {"experiment_id": 0, "priority_level": "MEDIUM", "decision": "optimize"},
                    "assumed_failure": "execution_plan_fails",
                    "failure_impact": "no_action_taken",
                }
            )

        parsed = {
            "admin_user": admin_user,
            "command_text": cmd,
            "mission_type": mission_type,
            "category": category,
            "required_capabilities": required_capabilities,
            "actions": actions,
        }

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO admin_commands (admin_user, command_text, mission_type, parsed_json, status)
                VALUES (?, ?, ?, ?, 'PARSED')
                """,
                (str(admin_user), cmd, mission_type, json.dumps(parsed)),
            )
            command_id = int(cursor.lastrowid)
            conn.commit()

        audit_log(actor=str(admin_user), action="admin.command.parsed", target=str(command_id), payload=parsed)
        return {"command_id": command_id, **parsed}

    def create_mission_from_command(self, *, command_id: int) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, parsed_json, status FROM admin_commands WHERE id=?", (int(command_id),))
            row = cursor.fetchone()
            if not row:
                return {"error": "command_not_found"}
            if str(row["status"]) == "MISSION_CREATED":
                return {"error": "mission_already_created", "command_id": int(command_id)}

            parsed = json.loads(str(row["parsed_json"] or "{}"))
            cursor.execute(
                """
                INSERT INTO mission_queue (command_id, goal, mission_type, required_capabilities_json, actions_json, status)
                VALUES (?, ?, ?, ?, ?, 'PENDING')
                """,
                (
                    int(command_id),
                    str(parsed.get("command_text") or ""),
                    str(parsed.get("mission_type") or "general"),
                    json.dumps(parsed.get("required_capabilities") or []),
                    json.dumps(parsed.get("actions") or []),
                ),
            )
            mission_id = int(cursor.lastrowid)
            cursor.execute("UPDATE admin_commands SET status='MISSION_CREATED' WHERE id=?", (int(command_id),))
            conn.commit()

        audit_log(actor="admin_command_engine", action="admin.command.mission_created", target=str(mission_id), payload={"command_id": command_id})
        return {"mission_id": mission_id, "status": "PENDING", "goal": parsed.get("command_text")}
