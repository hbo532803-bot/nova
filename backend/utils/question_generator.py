from __future__ import annotations

from typing import Any


def generate_adaptive_questions(service: str, details: dict[str, Any]) -> list[str]:
    questions: list[str] = []

    if not details.get("target_audience"):
        questions.append("Who is the target audience?")

    if not details.get("timeline"):
        questions.append("What is your desired launch timeline?")

    if not details.get("budget"):
        questions.append("What budget range should we optimize for?")

    if service == "website_development" and not details.get("pages"):
        questions.append("How many pages or core screens do you need?")

    if service == "lead_generation" and not details.get("lead_volume"):
        questions.append("How many qualified leads per month are you targeting?")

    if service == "business_automation" and not details.get("current_tools"):
        questions.append("Which tools/systems should be integrated?")

    return questions
