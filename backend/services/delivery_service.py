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
        intel = self._collect_intelligence(task_outputs)
        if kind == "website":
            website_intel = intel.get("website") or {}
            business_intel = intel.get("business") or {}
            marketing_intel = intel.get("marketing") or {}
            research_intel = intel.get("research") or {}

            html = self._extract_html(task_outputs)
            if not html:
                html = self._render_dynamic_website_html(
                    headline=str(website_intel.get("headline") or ""),
                    subheadline=str(website_intel.get("subheadline") or ""),
                    benefits=list(website_intel.get("benefits") or []),
                    sections=list(website_intel.get("sections") or []),
                    cta_text=str(website_intel.get("cta_text") or marketing_intel.get("cta_text") or ""),
                    form_fields=list(website_intel.get("form_fields") or []),
                    target_audience=str(business_intel.get("target_audience") or ""),
                    offer=str(business_intel.get("offer") or ""),
                    problems=list(research_intel.get("problems") or []),
                ) or self._fallback_website_html(task_outputs)
            return {
                "pages": max(1, self._extract_count(task_outputs, "page")),
                "html": html,
                "headline": str(website_intel.get("headline") or ""),
                "subheadline": str(website_intel.get("subheadline") or ""),
                "benefits": list(website_intel.get("benefits") or []),
                "cta_text": str(website_intel.get("cta_text") or marketing_intel.get("cta_text") or ""),
                "offer": str(business_intel.get("offer") or self._extract_first(task_outputs, ("offer", "package", "tier"))),
                "target_audience": str(business_intel.get("target_audience") or self._extract_first(task_outputs, ("audience", "customer", "icp"))),
                "monetization": str(business_intel.get("monetization") or self._extract_first(task_outputs, ("subscription", "pricing", "retainer", "monetization"))),
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
            business_intel = intel.get("business") or {}
            marketing_intel = intel.get("marketing") or {}
            return {
                "lead_items": self._extract_count(task_outputs, "lead"),
                "offer": str(business_intel.get("offer") or self._extract_first(task_outputs, ("offer", "package", "tier"))),
                "target_audience": str(business_intel.get("target_audience") or self._extract_first(task_outputs, ("audience", "customer", "icp"))),
                "monetization": str(business_intel.get("monetization") or self._extract_first(task_outputs, ("retainer", "pricing", "monetization"))),
                "lead_strategy": list(marketing_intel.get("lead_strategy") or []),
                "offer": self._extract_first(task_outputs, ("offer", "package", "tier")) or "Lead generation starter package",
                "target_audience": self._extract_first(task_outputs, ("audience", "customer", "icp")) or "B2B service businesses",
                "monetization": self._extract_first(task_outputs, ("retainer", "pricing", "monetization")) or "Pay-per-qualified-lead or monthly retainer",
                "artifacts": task_outputs,
            }
        if kind == "automation":
            business_intel = intel.get("business") or {}
            return {
                "workflows": self._extract_count(task_outputs, "workflow"),
                "offer": str(business_intel.get("offer") or self._extract_first(task_outputs, ("offer", "package", "tier"))),
                "target_audience": str(business_intel.get("target_audience") or self._extract_first(task_outputs, ("audience", "customer", "team"))),
                "monetization": str(business_intel.get("monetization") or self._extract_first(task_outputs, ("retainer", "pricing", "monetization"))),
                "artifacts": task_outputs,
            }
        business_intel = intel.get("business") or {}
        return {
            "offer": str(business_intel.get("offer") or self._extract_first(task_outputs, ("offer", "package", "tier"))),
            "target_audience": str(business_intel.get("target_audience") or self._extract_first(task_outputs, ("audience", "customer", "icp"))),
            "monetization": str(business_intel.get("monetization") or self._extract_first(task_outputs, ("subscription", "pricing", "retainer", "monetization"))),
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

    def _render_dynamic_website_html(
        self,
        *,
        headline: str,
        subheadline: str,
        benefits: list[str],
        sections: list[str],
        cta_text: str,
        form_fields: list[str],
        target_audience: str,
        offer: str,
        problems: list[str],
    ) -> str:
        if not headline or not target_audience or not offer:
            return ""
        clean_benefits = [b for b in benefits if isinstance(b, str) and b.strip()][:5]
        if len(clean_benefits) < 2:
            return ""
        clean_sections = [s for s in sections if isinstance(s, str) and s.strip()][:6]
        if not clean_sections:
            clean_sections = ["Hero", "Benefits", "Process", "Proof", "Lead Form"]
        clean_fields = [f for f in form_fields if isinstance(f, str) and f.strip()][:6] or ["name", "email", "goal"]
        fields_html = "".join(
            f"<label>{f.title()}<input name='{f}' /></label>" for f in clean_fields
        )
        probs = "".join(f"<li>{p}</li>" for p in problems[:3] if isinstance(p, str) and p.strip())
        ben_html = "".join(f"<li>{b}</li>" for b in clean_benefits)
        sec_html = "".join(f"<li>{s}</li>" for s in clean_sections)
        return (
            "<!doctype html><html><head><meta charset='utf-8'><title>Nova Dynamic Website</title></head><body>"
            f"<header><h1>{headline}</h1><p>{subheadline}</p><p><strong>Best for:</strong> {target_audience}</p><a href='#lead-form'>{cta_text or 'Get started'}</a></header>"
            f"<section><h2>Offer</h2><p>{offer}</p></section>"
            f"<section><h2>Problems we solve</h2><ul>{probs}</ul></section>"
            f"<section><h2>Benefits</h2><ul>{ben_html}</ul></section>"
            f"<section><h2>Page structure</h2><ul>{sec_html}</ul></section>"
            f"<section id='lead-form'><h2>Start now</h2><form>{fields_html}<button type='submit'>{cta_text or 'Submit'}</button></form></section>"
            "</body></html>"
        )

    def _collect_intelligence(self, task_outputs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = {
            "website": {},
            "business": {},
            "marketing": {},
            "research": {},
        }
        for item in task_outputs:
            self._merge_intel_from_value(item.get("output"), buckets)
        return buckets

    def _merge_intel_from_value(self, value: Any, buckets: dict[str, dict[str, Any]]) -> None:
        if isinstance(value, dict):
            for k in ("website", "business", "marketing", "research"):
                blob = value.get(k)
                if isinstance(blob, dict):
                    buckets[k].update({kk: vv for kk, vv in blob.items() if vv not in (None, "", [], {})})
            for v in value.values():
                self._merge_intel_from_value(v, buckets)
        elif isinstance(value, list):
            for v in value:
                self._merge_intel_from_value(v, buckets)

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
            headline = str(output.get("headline") or "").strip()
            offer = str(output.get("offer") or "").strip()
            audience = str(output.get("target_audience") or "").strip()
            if pages <= 0:
                return {"ok": False, "error": "pages == 0"}
            if len(re.sub(r"<[^>]+>", " ", html).strip()) < 120:
                return {"ok": False, "error": "website content is too thin"}
            if "<form" not in html.lower():
                return {"ok": False, "error": "website missing lead form"}
            if not headline or len(headline.split()) < 4:
                return {"ok": False, "error": "website headline not customized"}
            if not offer or not audience:
                return {"ok": False, "error": "website missing business context"}
            if headline.lower() in {"launch faster with nova", "nova delivery"}:
                return {"ok": False, "error": "website headline is generic"}
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
            if "generic" in val:
                return {"ok": False, "error": f"generic {field}"}
        return {"ok": True}
