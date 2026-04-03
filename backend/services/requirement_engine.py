from __future__ import annotations

from typing import Any

from backend.utils.intent_parser import parse_intent
from backend.utils.question_generator import generate_adaptive_questions


class RequirementEngineService:
    """
    User-facing requirement intake service.
    Produces structured requirements and offer suggestions.
    """

    def build_requirement(self, user_input: str, provided: dict[str, Any] | None = None) -> dict[str, Any]:
        provided = provided or {}
        intent = parse_intent(user_input)

        goal = (provided.get("goal") or user_input or "Define project requirement").strip()

        details: dict[str, Any] = {
            "intent": intent.intent,
            "target_audience": provided.get("target_audience"),
            "timeline": provided.get("timeline"),
            "budget": provided.get("budget"),
            "pages": provided.get("pages"),
            "lead_volume": provided.get("lead_volume"),
            "current_tools": provided.get("current_tools"),
            "notes": provided.get("notes"),
        }

        missing_questions = generate_adaptive_questions(intent.service, details)
        details["questions"] = missing_questions
        details["offers"] = self._build_offers(intent.service, goal, details)

        confidence = max(40, intent.confidence - (len(missing_questions) * 5))

        return {
            "service": intent.service,
            "goal": goal,
            "details": details,
            "confidence": confidence,
        }

    def _build_offers(self, service: str, goal: str, details: dict[str, Any]) -> list[dict[str, Any]]:
        base_scope = self._scope_for_service(service)
        timeline = details.get("timeline") or "4-8 weeks"

        return [
            {
                "tier": "BASIC",
                "plan": f"Starter delivery for {goal}",
                "estimated_price": "$1,500",
                "execution_scope": {
                    "service": service,
                    "timeline": timeline,
                    "deliverables": base_scope[:2],
                },
            },
            {
                "tier": "STANDARD",
                "plan": f"Recommended balanced implementation for {goal}",
                "estimated_price": "$4,000",
                "execution_scope": {
                    "service": service,
                    "timeline": timeline,
                    "deliverables": base_scope[:3],
                },
            },
            {
                "tier": "PREMIUM",
                "plan": f"Full-system implementation and optimization for {goal}",
                "estimated_price": "$9,000",
                "execution_scope": {
                    "service": service,
                    "timeline": timeline,
                    "deliverables": base_scope,
                },
            },
        ]

    def _scope_for_service(self, service: str) -> list[str]:
        map_scope = {
            "website_development": [
                "requirements workshop",
                "UX/content structure",
                "responsive frontend build",
                "deployment and QA",
            ],
            "lead_generation": [
                "ICP definition",
                "outreach channel setup",
                "lead pipeline automation",
                "conversion reporting",
            ],
            "business_automation": [
                "process mapping",
                "integration design",
                "workflow implementation",
                "monitoring and optimization",
            ],
            "marketing_growth": [
                "channel strategy",
                "campaign setup",
                "creative/testing loop",
                "performance analytics",
            ],
            "consultation": [
                "discovery session",
                "solution blueprint",
                "execution roadmap",
                "handoff",
            ],
        }
        return map_scope.get(service, map_scope["consultation"])
