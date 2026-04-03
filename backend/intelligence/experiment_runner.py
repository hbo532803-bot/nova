from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from backend.database import get_db
from backend.frontend_api.event_bus import broadcast
from backend.tools.tool_sandbox import ToolSandbox
from backend.tools.web_access import safe_get
from backend.tools.sandbox_shell import safe_execute
from backend.tools.diff_engine import apply_change
from backend.tools.rollback_manager import rollback_last
from backend.intelligence.experiment_metrics import ExperimentMetricsStore
from backend.knowledge.graph_store import KnowledgeGraphStore


class ExperimentRunner:
    """
    Controlled experiment execution runner.
    Runs inside guardrails using ToolSandbox + allowed tools registry:
    - web_access.safe_get
    - sandbox_shell.safe_execute

    Produces simple metrics and stores them on economic_experiments.
    """

    def __init__(self):
        self.sandbox = ToolSandbox(timeout_sec=5)
        self.metrics = ExperimentMetricsStore()
        self.kg = KnowledgeGraphStore()

    def run(self, experiment_id: int) -> Dict[str, Any]:
        exp = self._load_experiment(experiment_id)
        if not exp:
            return {"error": "experiment_not_found"}

        name = exp["name"]
        broadcast({"type": "log", "level": "info", "message": f"ExperimentRunner starting: {name} (id={experiment_id})"})

        playbook = self._load_playbook(experiment_id) or self._default_playbook(exp)
        stage = self._select_stage(experiment_id, playbook)
        stage_name = str(stage.get("name") or "single")
        executed = []
        rollback_stack = []

        try:
            steps = stage.get("actions") if isinstance(stage, dict) else None
            for step in (steps or playbook.get("actions", [])):
                result = self._run_step(step)
                executed.append({"step": step, "result": result})
                if isinstance(result, dict) and result.get("backup"):
                    rollback_stack.append({"type": "ROLLBACK_FILE", "path": step.get("path")})

            metrics = self._evaluate_metrics(experiment_id, playbook, executed)
            criteria = (stage.get("success_criteria") or {}) if isinstance(stage, dict) else {}
            success = self._meets_criteria(metrics, criteria)
            validation = float(metrics.get("validation_score", 0))
            revenue = float(metrics.get("revenue_generated", 0))
            cost = float(metrics.get("cost_incurred", 0))

            status_hint = str(stage.get("lifecycle_status") or ("TESTING" if success else "FAILED"))
            self._store_metrics(experiment_id, success, validation, revenue, cost, notes=f"stage:{stage_name}")
            self._set_status(experiment_id, status_hint if success else "FAILED")
            self._record_metric_bundle(experiment_id, metrics)
            self.metrics.record(experiment_id, "stage_success", 1.0 if success else 0.0, source="runner")
            self._advance_stage(experiment_id, playbook, success)
            self._write_knowledge_graph(experiment_id, playbook, stage_name, metrics, success)

            return {
                "experiment_id": experiment_id,
                "success": success,
                "objective": playbook.get("objective"),
                "stage": stage_name,
                "executed_steps": executed,
                "metrics": metrics,
            }

        except Exception as e:
            broadcast({"type": "log", "level": "error", "message": f"ExperimentRunner failed: {e}"})
            self._attempt_rollback(rollback_stack)
            self._store_metrics(experiment_id, False, 10, 0.0, 1.0, notes=f"playbook_failed:{e}")
            self.metrics.record(experiment_id, "runner_failure", 1.0, source="runner")
            return {"experiment_id": experiment_id, "success": False, "error": str(e), "executed_steps": executed}

    def _run_step(self, step: Dict[str, Any]) -> Any:
        step_type = str(step.get("type"))

        if step_type == "WEB_GET":
            url = str(step.get("url"))
            return {"url": url, "body": self.sandbox.run(safe_get, url)}

        if step_type == "SHELL_SAFE":
            cmd = str(step.get("command"))
            return {"command": cmd, "output": self.sandbox.run(safe_execute, cmd)}

        if step_type == "DIFF_APPLY":
            path = str(step.get("path"))
            new_content = str(step.get("new_content"))
            return apply_change(path, new_content)

        if step_type == "METRIC_SET":
            metrics = step.get("metrics") or {}
            if not isinstance(metrics, dict):
                raise RuntimeError("METRIC_SET requires metrics dict")
            return {"metrics": metrics}

        raise RuntimeError(f"Unknown playbook step type: {step_type}")

    def _attempt_rollback(self, stack: list[dict]) -> None:
        for item in reversed(stack):
            if item.get("type") == "ROLLBACK_FILE":
                try:
                    rollback_last(str(item.get("path")))
                except Exception:
                    pass

    def _load_experiment(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM economic_experiments WHERE id=?", (experiment_id,))
            row = cursor.fetchone()
        return dict(row) if row else None

    def _load_playbook(self, experiment_id: int) -> Optional[Dict[str, Any]]:
        """
        Playbooks are stored in system_settings to avoid altering core tables.
        Key: experiment_playbook_<id>
        """
        key = f"experiment_playbook_{experiment_id}"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_settings WHERE key=?", (key,))
            row = cursor.fetchone()
        if not row or not row["value"]:
            return None
        try:
            return json.loads(str(row["value"]))
        except Exception:
            return None

    def _default_playbook(self, exp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default safe playbook (no file modifications by default).
        """
        return {
            "objective": f"Validate feasibility signals for {exp.get('name')}",
            "actions": [
                {"type": "WEB_GET", "url": "https://api.github.com"},
                {"type": "SHELL_SAFE", "command": "echo experiment check"},
            ],
            "metrics": ["traffic", "conversions", "revenue_signals", "engagement"],
            "rollback": {"strategy": "none"},
        }

    def _select_stage(self, experiment_id: int, playbook: Dict[str, Any]) -> Dict[str, Any]:
        stages = playbook.get("stages")
        if not isinstance(stages, list) or not stages:
            return {"name": "single", "actions": playbook.get("actions", []), "success_criteria": {"validation_score_gte": 55}}

        idx = 0
        key = f"experiment_stage_{experiment_id}"
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key=?", (key,))
                row = cursor.fetchone()
            if row and row["value"]:
                blob = json.loads(str(row["value"]))
                idx = int(blob.get("idx") or 0)
        except Exception:
            idx = 0

        idx = max(0, min(idx, len(stages) - 1))
        stage = stages[idx]
        return stage if isinstance(stage, dict) else {"name": f"stage_{idx}", "actions": []}

    def _advance_stage(self, experiment_id: int, playbook: Dict[str, Any], success: bool) -> None:
        stages = playbook.get("stages")
        if not isinstance(stages, list) or not stages:
            return
        if not success:
            return

        key = f"experiment_stage_{experiment_id}"
        idx = 0
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key=?", (key,))
                row = cursor.fetchone()
            if row and row["value"]:
                blob = json.loads(str(row["value"]))
                idx = int(blob.get("idx") or 0)
        except Exception:
            idx = 0

        next_idx = idx + 1
        if next_idx >= len(stages):
            # Completed all stages
            self._set_status(experiment_id, "LIVE")
            next_idx = len(stages) - 1

        payload = {"idx": next_idx, "updated_at": datetime.utcnow().isoformat()}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                (key, json.dumps(payload)),
            )
            conn.commit()

    def _meets_criteria(self, metrics: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        ok = bool(metrics.get("success"))
        try:
            if "validation_score_gte" in criteria:
                ok = ok and float(metrics.get("validation_score") or 0) >= float(criteria["validation_score_gte"])
        except Exception:
            pass
        return ok

    def _evaluate_metrics(self, experiment_id: int, playbook: Dict[str, Any], executed: list[dict]) -> Dict[str, Any]:
        """
        Real-world metric collection will evolve; for now we compute bounded signals:
        - traffic: 1 if web step returned content
        - conversions: 0 (not available yet)
        - revenue_signals: 0 (not available yet)
        - engagement: 1 if shell step succeeded
        """
        web_ok = any((s.get("result") or {}).get("body") for s in executed if (s.get("step") or {}).get("type") == "WEB_GET")
        shell_ok = any((s.get("result") or {}).get("output") for s in executed if (s.get("step") or {}).get("type") == "SHELL_SAFE")

        injected = {}
        for s in executed:
            if (s.get("step") or {}).get("type") == "METRIC_SET":
                injected.update(((s.get("result") or {}).get("metrics") or {}))

        traffic = float(injected.get("traffic")) if "traffic" in injected else (1.0 if web_ok else 0.0)
        engagement = float(injected.get("engagement")) if "engagement" in injected else (1.0 if shell_ok else 0.0)
        conversions = float(injected.get("conversions") or 0.0)
        revenue_signals = float(injected.get("revenue_signals") or 0.0)

        success = bool(web_ok or shell_ok)
        validation = (traffic * 30.0) + (engagement * 30.0) + (conversions * 20.0) + (revenue_signals * 20.0)
        validation = max(0.0, min(100.0, validation))

        return {
            "success": success,
            "validation_score": validation,
            "traffic": traffic,
            "conversions": conversions,
            "revenue_signals": revenue_signals,
            "engagement": engagement,
            "revenue_generated": 0.0,
            "cost_incurred": 1.0,
        }

    def _record_metric_bundle(self, experiment_id: int, metrics: Dict[str, Any]) -> None:
        for k in ("traffic", "conversions", "revenue_signals", "engagement"):
            if k in metrics:
                self.metrics.record(experiment_id, k, float(metrics[k]), source="runner")

    def _store_metrics(
        self,
        experiment_id: int,
        success: bool,
        validation_score: float,
        revenue_generated: float,
        cost_incurred: float,
        *,
        notes: str,
    ) -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE economic_experiments
                SET status = ?,
                    validation_score = ?,
                    revenue_generated = revenue_generated + ?,
                    cost_incurred = cost_incurred + ?,
                    last_tested = ?,
                    notes = ?
                WHERE id = ?
                """,
                (
                    "TESTING" if success else "FAILED",
                    validation_score,
                    revenue_generated,
                    cost_incurred,
                    datetime.utcnow(),
                    notes,
                    experiment_id,
                ),
            )
            conn.commit()

    def _set_status(self, experiment_id: int, status: str) -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE economic_experiments SET status=? WHERE id=?", (status, experiment_id))
            conn.commit()

    def _write_knowledge_graph(
        self,
        experiment_id: int,
        playbook: Dict[str, Any],
        stage: str,
        metrics: Dict[str, Any],
        success: bool,
    ) -> None:
        try:
            node_key = str(experiment_id)
            self.kg.upsert_node(
                "experiment",
                node_key,
                {
                    "objective": str(playbook.get("objective") or ""),
                    "stage": stage,
                    "success": bool(success),
                    "validation_score": float(metrics.get("validation_score") or 0),
                    "signals": {
                        "traffic": float(metrics.get("traffic") or 0),
                        "engagement": float(metrics.get("engagement") or 0),
                        "conversions": float(metrics.get("conversions") or 0),
                        "revenue_signals": float(metrics.get("revenue_signals") or 0),
                    },
                },
            )
            outcome_key = "success" if success else "failure"
            self.kg.upsert_node("outcome", outcome_key, {"label": outcome_key})
            self.kg.add_edge("experiment", node_key, "HAS_OUTCOME", "outcome", outcome_key)
        except Exception:
            pass

