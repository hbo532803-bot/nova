from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any
from backend.database import get_db


class WebsiteDeployer:
    """
    Minimal website deployer: persists HTML locally and returns file URL/path.
    """

    def __init__(self, base_dir: str = "backend/memory/deployments/websites"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def deploy(self, output: dict[str, Any], *, mission_id: str = "") -> dict[str, Any]:
        html = self._extract_html(output, mission_id=mission_id)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        file_path = self.base_dir / f"website_{stamp}.html"
        file_path.write_text(html, encoding="utf-8")
        if mission_id:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    (f"mission_site_{mission_id}", str(file_path)),
                )
                conn.commit()
        public_base = os.getenv("NOVA_PUBLIC_BASE", "http://localhost:8000").rstrip("/")

        return {
            "deployer": "website_deployer",
            "status": "deployed",
            "target": "local_file",
            "path": str(file_path),
            "url": file_path.resolve().as_uri(),
            "mission_id": mission_id,
            "share_url": f"{public_base}/api/landing/{mission_id}" if mission_id else "",
        }

    @staticmethod
    def _extract_html(output: dict[str, Any], *, mission_id: str = "") -> str:
        candidate = output.get("html") if isinstance(output, dict) else None
        if isinstance(candidate, str) and candidate.strip():
            return WebsiteDeployer._inject_runtime(candidate, mission_id=mission_id)

        title = "Nova Website Output"
        body = "<p>Generated website artifact.</p>"
        base = f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head><body>{body}</body></html>"
        return WebsiteDeployer._inject_runtime(base, mission_id=mission_id)

    @staticmethod
    def _inject_runtime(html: str, *, mission_id: str = "") -> str:
        runtime = f"""
<script>
window.NOVA_MISSION_ID = "{mission_id}";
async function novaTrack(eventType, extra) {{
  const payload = Object.assign({{ mission_id: window.NOVA_MISSION_ID || "", event_type: eventType, source: "landing_runtime" }}, extra || {{}});
  try {{
    await fetch('/api/signals/track', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(payload)}});
  }} catch (_) {{}}
}}
async function novaSubmitLead(e) {{
  e.preventDefault();
  const f = e.target;
  const payload = {{
    mission_id: window.NOVA_MISSION_ID || "",
    source: "landing_form",
    name: (f.querySelector('[name=name]')||{{value:''}}).value,
    email: (f.querySelector('[name=email]')||{{value:''}}).value,
    phone: (f.querySelector('[name=phone]')||{{value:''}}).value,
  }};
  const r = await fetch('/api/leads', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(payload)}});
  const data = await r.json();
  alert(data.ok ? 'Thanks! We will contact you shortly.' : (data.detail || 'Lead submit failed'));
}}
async function novaCheckout() {{
  await novaTrack('click', {{ reason:'checkout_button_click' }});
  const payload = {{ mission_id: window.NOVA_MISSION_ID || "", amount: 499 }};
  const r = await fetch('/api/checkout/simulate', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(payload)}});
  const data = await r.json();
  alert(data.ok ? 'Checkout simulated. Order created.' : (data.detail || 'Checkout failed'));
}}
document.addEventListener('DOMContentLoaded', () => {{
  const form = document.querySelector('form');
  if (form) form.addEventListener('submit', async (e) => {{ await novaTrack('click', {{ reason:'form_submit_click' }}); return novaSubmitLead(e); }});
  const btn = document.getElementById('nova-checkout-btn');
  if (btn) btn.addEventListener('click', novaCheckout);
}});
</script>
"""
        if "</body>" in html:
            return html.replace("</body>", "<button id='nova-checkout-btn' type='button'>Get full service</button>" + runtime + "</body>")
        return html + runtime
