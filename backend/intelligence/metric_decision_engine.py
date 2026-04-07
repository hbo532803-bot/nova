from __future__ import annotations

from typing import Any


class MetricDecisionEngine:
    """
    Threshold-based decisions for predictable, data-driven outcomes.
    """

    def __init__(self, *, scale_conversion_rate: float = 0.05, min_ctr: float = 0.01):
        self.scale_conversion_rate = float(scale_conversion_rate)
        self.min_ctr = float(min_ctr)

    def decide(self, metrics_payload: dict[str, Any]) -> dict[str, Any]:
        metrics = metrics_payload.get("metrics") or {}
        real = metrics_payload.get("real") or {}

        conversion_rate = float(metrics.get("conversion_rate") or 0.0)
        ctr = float(metrics.get("click_through_rate") or 0.0)
        page_views = int(real.get("page_views") or 0)
        leads = int(real.get("leads") or 0)

        if conversion_rate >= self.scale_conversion_rate and leads >= 3:
            return {"decision": "scale", "reason": "conversion_rate_above_threshold"}

        if page_views >= 100 and leads == 0:
            return {"decision": "fail", "reason": "high_traffic_zero_leads"}

        if ctr < self.min_ctr and page_views >= 50:
            return {"decision": "optimize", "reason": "ctr_below_threshold"}

        return {"decision": "hold", "reason": "insufficient_or_mixed_signal"}
