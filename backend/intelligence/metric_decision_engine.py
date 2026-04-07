from __future__ import annotations

from typing import Any


class MetricDecisionEngine:
    """
    Threshold-based decisions with reliability gate.
    """

    def __init__(self, *, scale_conversion_rate: float = 0.05, min_ctr: float = 0.01):
        self.scale_conversion_rate = float(scale_conversion_rate)
        self.min_ctr = float(min_ctr)

    def decide(self, metrics_payload: dict[str, Any]) -> dict[str, Any]:
        metrics = metrics_payload.get("metrics") or {}
        real = metrics_payload.get("real") or {}
        reliability = metrics_payload.get("reliability") or {}

        conversion_rate = float(metrics.get("conversion_rate") or 0.0)
        ctr = float(metrics.get("click_through_rate") or 0.0)
        page_views = int(real.get("page_views") or 0)
        leads = int(real.get("leads") or 0)
        reliable = bool(reliability.get("is_data_reliable", False))
        threshold = int(reliability.get("min_sample_threshold") or 50)

        if not reliable or page_views < threshold:
            return {
                "decision": "gather_more_data",
                "reason": "insufficient_reliable_sample",
                "requires_more_views": max(0, threshold - page_views),
            }

        if conversion_rate >= self.scale_conversion_rate and leads >= 3:
            return {"decision": "scale", "reason": "conversion_rate_above_threshold"}

        if page_views >= max(100, threshold) and leads == 0:
            return {"decision": "fail", "reason": "high_traffic_zero_leads"}

        if ctr < self.min_ctr and page_views >= threshold:
            return {"decision": "optimize", "reason": "ctr_below_threshold"}

        return {"decision": "hold", "reason": "reliable_but_not_ready"}
