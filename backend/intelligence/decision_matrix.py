from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

from backend.intelligence.confidence_engine import ConfidenceEngine
from backend.database import get_db
import json

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SystemImpact = Literal["POSITIVE", "NEUTRAL", "NEGATIVE"]
DecisionOutcome = Literal[
    "APPROVED",
    "REJECTED",
    "REQUIRES_HUMAN_APPROVAL",
    "PLANNING_ONLY",
]


@dataclass(frozen=True)
class DecisionFactors:
    economic_potential: int  # 0-10
    risk_level: RiskLevel
    confidence_score: int  # 0-100
    resource_cost: int  # 0-10
    system_impact: SystemImpact
    learning_value: int  # 0-10


class DecisionMatrix:
    """
    Implements docs/NOVA_DECISION_MATRIX.md.
    Produces a decision outcome plus a compact reasoning summary.
    """

    def __init__(self):
        self.confidence = ConfidenceEngine()

    def evaluate(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        factors = self._evaluate_factors(plan)
        outcome, reasoning = self._apply_rules(factors)
        return {
            "outcome": outcome,
            "factors": {
                "economic_potential": factors.economic_potential,
                "risk_level": factors.risk_level,
                "confidence_score": factors.confidence_score,
                "resource_cost": factors.resource_cost,
                "system_impact": factors.system_impact,
                "learning_value": factors.learning_value,
            },
            "reasoning": reasoning,
        }

    def _evaluate_factors(self, plan: Dict[str, Any]) -> DecisionFactors:
        """
        Minimal, non-speculative factor estimation from existing plan structure.
        If the plan provides explicit hints, we honor them. Otherwise we infer
        conservatively from steps.
        """
        state = self.confidence.get_state()
        confidence_score = int(state["score"])

        # Allow explicit factor overrides (from future planners).
        hints: Dict[str, Any] = plan.get("decision_hints", {}) or {}

        steps = [str(s).lower() for s in (plan.get("steps") or [])]
        actions = plan.get("actions") or []

        economic_potential = int(hints.get("economic_potential", 5))
        learning_value = int(hints.get("learning_value", 5))
        resource_cost = int(hints.get("resource_cost", 3))
        system_impact: SystemImpact = str(hints.get("system_impact", "NEUTRAL")).upper()  # type: ignore[assignment]

        # Strategy adjustments (learned) can bias risk/economic interpretation.
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key='strategy_adjustments'")
                row = cursor.fetchone()
            if row and row["value"]:
                blob = json.loads(str(row["value"]))
                adjustments = blob.get("adjustments") or []
                for a in adjustments:
                    if a.get("key") == "risk_bias" and str(a.get("value")).upper() == "LOW":
                        resource_cost = max(resource_cost, 4)
                        learning_value = max(learning_value, 6)
                    if a.get("key") == "risk_bias" and str(a.get("value")).upper() == "HIGH":
                        economic_potential = max(economic_potential, 6)
                    if a.get("key") == "exploration_mode" and bool(a.get("value")) is True:
                        learning_value = max(learning_value, 7)
                meta = blob.get("meta") or {}
                lt = meta.get("long_term") or {}
                if str(lt.get("trend") or "").lower() == "down":
                    # When long-term success is dropping, require more learning value to proceed.
                    learning_value = max(learning_value, 7)
        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in decision_matrix.py")

        risk_level: RiskLevel
        if "sandbox_shell" in steps or "deploy" in steps:
            risk_level = "HIGH"
        elif "market_scan" in steps or "experiment" in steps:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Data-informed scoring for opportunity and experiments
        try:
            if actions:
                a0 = actions[0]
                at = str(a0.get("type", "")).upper()
                payload = a0.get("payload") or {}

                if at in ("OPPORTUNITY_CONVERT", "OPPORTUNITY_APPROVE", "OPPORTUNITY_REJECT"):
                    pid = int(payload.get("proposal_id"))
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT cash_score, proposed_budget FROM market_proposals WHERE id=?",
                            (pid,),
                        )
                        row = cursor.fetchone()
                    if row:
                        cash = float(row["cash_score"] or 0)
                        budget = float(row["proposed_budget"] or 0)
                        # cash_score 0-100 -> economic_potential 0-10
                        economic_potential = max(economic_potential, int(min(10, cash / 10)))
                        # budget -> resource cost (0-10) relative to 0..5000
                        resource_cost = max(resource_cost, int(min(10, budget / 500)))
                        learning_value = max(learning_value, 6)

                if at == "EXPERIMENT_RUN":
                    exp_id = int(payload.get("experiment_id"))
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT roi, capital_allocated FROM economic_experiments WHERE id=?", (exp_id,))
                        row = cursor.fetchone()
                    if row:
                        roi = float(row["roi"] or 0)
                        cap = float(row["capital_allocated"] or 0)
                        # ROI -> economic potential
                        if roi > 0.5:
                            economic_potential = max(economic_potential, 8)
                        elif roi > 0.2:
                            economic_potential = max(economic_potential, 6)
                        elif roi < 0:
                            economic_potential = min(economic_potential, 3)
                        resource_cost = max(resource_cost, int(min(10, cap / 500)))
                        learning_value = max(learning_value, 7)

        except Exception:
            logging.getLogger(__name__).exception("Suppressed exception in decision_matrix.py")

        # Explicit risk override if provided.
        risk_level = str(hints.get("risk_level", risk_level)).upper()  # type: ignore[assignment]
        if risk_level not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            risk_level = "MEDIUM"

        if system_impact not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
            system_impact = "NEUTRAL"

        # Clamp ranges to constitution.
        economic_potential = max(0, min(10, economic_potential))
        learning_value = max(0, min(10, learning_value))
        resource_cost = max(0, min(10, resource_cost))
        confidence_score = max(0, min(100, confidence_score))

        return DecisionFactors(
            economic_potential=economic_potential,
            risk_level=risk_level,
            confidence_score=confidence_score,
            resource_cost=resource_cost,
            system_impact=system_impact,
            learning_value=learning_value,
        )

    def _apply_rules(self, f: DecisionFactors) -> tuple[DecisionOutcome, str]:
        # Rule: CRITICAL risk => reject
        if f.risk_level == "CRITICAL":
            return "REJECTED", "Rejected: CRITICAL risk"

        # Rule: negative system impact => reject
        if f.system_impact == "NEGATIVE":
            return "REJECTED", "Rejected: negative system impact"

        # Rule: confidence < 50 => planning only
        if f.confidence_score < 50:
            return "PLANNING_ONLY", "Planning only: confidence < 50"

        # Rule: HIGH risk requires >= 70 confidence
        if f.risk_level == "HIGH" and f.confidence_score < 70:
            return "REJECTED", "Rejected: HIGH risk and confidence < 70"

        # Rule: low economic potential + low learning => reject
        if f.economic_potential < 3 and f.learning_value < 4:
            return "REJECTED", "Rejected: low economic potential and low learning value"

        # Rule: moderate confidence requires human approval
        if 50 <= f.confidence_score < 70:
            return "REQUIRES_HUMAN_APPROVAL", "Requires approval: confidence 50–69"

        # Rule: high economic potential + low risk => approve
        if f.economic_potential >= 7 and f.risk_level == "LOW":
            return "APPROVED", "Approved: high economic potential and LOW risk"

        # Default approve when above autonomy threshold and not rejected.
        return "APPROVED", "Approved: passed decision matrix constraints"

