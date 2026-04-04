from __future__ import annotations

import re
from typing import Any

from backend.services.deployment_router import DeploymentRouter


class DeliveryService:
    """
    Maps aggregated task outputs into a user-facing final delivery object.
    """

    def __init__(self):
        self.deployment_router = DeploymentRouter()

    def build_final_result(self, aggregated: dict[str, Any], *, type_hint: str | None = None) -> dict[str, Any]:
        task_outputs = aggregated.get("task_outputs") or []
        kind = self._detect_type(type_hint, task_outputs)
        output = self._map_output(kind, task_outputs)
        validation = self._validate_output(kind, output)

        final_result = {
            "type": kind,
            "status": "completed" if validation["ok"] else "failed",
            "output": output,
            "meta": {
                "mission_id": aggregated.get("mission_id"),
                "order_id": aggregated.get("order_id"),
                "task_count": len(task_outputs),
            },
            "validation": validation,
        }
        if not validation["ok"]:
            final_result["error"] = validation["error"]
            final_result["deployment"] = {"status": "skipped", "reason": "validation_failed"}
            return final_result
        final_result["deployment"] = self.deployment_router.deploy(final_result)
        return final_result

    def _detect_type(self, type_hint: str | None, task_outputs: list[dict[str, Any]]) -> str:
        hint = (type_hint or "").lower()
        if "website" in hint:
            return "website"
        if "lead" in hint:
            return "leads"
        if "automation" in hint or "workflow" in hint:
            return "automation"

        blob = " ".join(str(item.get("output")) for item in task_outputs).lower()
        if "website" in blob or "landing" in blob:
            return "website"
        if "lead" in blob or "prospect" in blob:
            return "leads"
        if "automation" in blob or "workflow" in blob:
            return "automation"
        return "generic"

    def _map_output(self, kind: str, task_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        if kind == "website":
            html = self._extract_html(task_outputs)
            if not html:
                html = self._fallback_website_html(task_outputs)
            return {
                "pages": max(1, self._extract_count(task_outputs, "page")),
                "html": html,
                "offer": self._extract_first(task_outputs, ("offer", "package", "tier")) or "Starter website + lead form",
                "target_audience": self._extract_first(task_outputs, ("audience", "customer", "icp")) or "Small businesses validating demand",
                "monetization": self._extract_first(task_outputs, ("subscription", "pricing", "retainer", "monetization")) or "Monthly retainer with optional setup fee",
                "artifacts": task_outputs,
            }
        if kind == "leads":
            return {
                "lead_items": self._extract_count(task_outputs, "lead"),
                "offer": self._extract_first(task_outputs, ("offer", "package", "tier")) or "Lead generation starter package",
                "target_audience": self._extract_first(task_outputs, ("audience", "customer", "icp")) or "B2B service businesses",
                "monetization": self._extract_first(task_outputs, ("retainer", "pricing", "monetization")) or "Pay-per-qualified-lead or monthly retainer",
                "artifacts": task_outputs,
            }
        if kind == "automation":
            return {
                "workflows": self._extract_count(task_outputs, "workflow"),
                "offer": self._extract_first(task_outputs, ("offer", "package", "tier")) or "Workflow automation implementation",
                "target_audience": self._extract_first(task_outputs, ("audience", "customer", "team")) or "Operators with repetitive manual workflows",
                "monetization": self._extract_first(task_outputs, ("retainer", "pricing", "monetization")) or "One-time setup + maintenance plan",
                "artifacts": task_outputs,
            }
        return {
            "offer": self._extract_first(task_outputs, ("offer", "package", "tier")) or "Consulting strategy sprint",
            "target_audience": self._extract_first(task_outputs, ("audience", "customer", "icp")) or "Founders needing validated growth direction",
            "monetization": self._extract_first(task_outputs, ("subscription", "pricing", "retainer", "monetization")) or "Fixed-fee sprint then monthly advisory",
            "artifacts": task_outputs,
        }

    @staticmethod
    def _extract_count(task_outputs: list[dict[str, Any]], token: str) -> int:
        token = token.lower()
        return sum(1 for item in task_outputs if token in str(item.get("output", "")).lower())

    def _extract_html(self, task_outputs: list[dict[str, Any]]) -> str:
        for item in task_outputs:
            out = item.get("output")
            if isinstance(out, dict):
                html = out.get("html")
                if isinstance(html, str) and "<html" in html.lower():
                    return html
            text = str(out or "")
            if "<html" in text.lower():
                return text
        return ""

    def _fallback_website_html(self, task_outputs: list[dict[str, Any]]) -> str:
        headline = self._extract_first(task_outputs, ("headline", "offer", "value")) or "Launch Faster With Nova"
        sub = self._extract_first(task_outputs, ("problem", "pain", "challenge")) or "We turn vague ideas into a conversion-ready website."
        cta = self._extract_first(task_outputs, ("cta", "book", "demo")) or "Book a free strategy call"
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Nova Delivery</title></head><body>"
            f"<header><h1>{headline}</h1><p>{sub}</p><a href='#lead-form'>{cta}</a></header>"
            "<section><h2>What you get</h2><ul><li>Offer positioning</li><li>Trust-building sections</li><li>Lead capture flow</li></ul></section>"
            "<section><h2>Who this is for</h2><p>Founders and operators who need measurable lead generation.</p></section>"
            "<section><h2>Pricing</h2><p>One-time build + optional monthly optimization.</p></section>"
            "<section id='lead-form'><h2>Get started</h2><form><label>Name<input name='name'/></label><label>Email<input name='email' type='email'/></label><button type='submit'>Get proposal</button></form></section>"
            "</body></html>"
        )

    def _extract_first(self, task_outputs: list[dict[str, Any]], hints: tuple[str, ...]) -> str:
        hints_l = tuple(h.lower() for h in hints)
        for item in task_outputs:
            blob = str(item.get("output") or "")
            low = blob.lower()
            if any(h in low for h in hints_l):
                return blob[:180]
        return ""

    def _validate_output(self, kind: str, output: dict[str, Any]) -> dict[str, Any]:
        if kind == "website":
            pages = int(output.get("pages") or 0)
            html = str(output.get("html") or "")
            if pages <= 0:
                return {"ok": False, "error": "pages == 0"}
            if len(re.sub(r"<[^>]+>", " ", html).strip()) < 120:
                return {"ok": False, "error": "website content is too thin"}
            if "<form" not in html.lower():
                return {"ok": False, "error": "website missing lead form"}
            return {"ok": True}

        artifacts = output.get("artifacts") or []
        if not isinstance(artifacts, list) or not artifacts:
            return {"ok": False, "error": "no task artifacts"}
        for field in ("offer", "target_audience", "monetization"):
            val = str(output.get(field) or "").strip().lower()
            if not val:
                return {"ok": False, "error": f"missing {field}"}
            if val in {"n/a", "none", "unknown", "null"}:
                return {"ok": False, "error": f"invalid {field}"}
        return {"ok": True}
