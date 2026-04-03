from __future__ import annotations

from typing import Any, Dict


def list_playbooks() -> Dict[str, Dict[str, Any]]:
    """
    Structured playbook library for common experiment types.
    These are templates; they become concrete by attaching to an experiment id.
    """
    return {
        "saas_validation": {
            "objective": "Validate demand for a SaaS niche using lightweight signal checks.",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["discover", "validate"]},
            "stages": [
                {
                    "name": "discover",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://news.ycombinator.com"},
                        {"type": "WEB_GET", "url": "https://www.producthunt.com"},
                        {"type": "SHELL_SAFE", "command": "echo collect problem+buyer signals"},
                    ],
                    "metrics": ["traffic", "engagement"],
                    "success_criteria": {"validation_score_gte": 55},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "validate",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo define value prop + ICP"},
                        {"type": "METRIC_SET", "metrics": {"conversions": 0.0, "revenue_signals": 0.0}},
                        {"type": "SHELL_SAFE", "command": "echo define pricing + willingness-to-pay probes"},
                    ],
                    "metrics": ["conversions", "revenue_signals", "engagement"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
            ],
            "metrics": ["traffic", "conversions", "revenue_signals", "engagement"],
            "rollback": {"strategy": "none"},
        },
        "lead_generation": {
            "objective": "Validate lead generation potential for a target niche.",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["research", "offer_test"]},
            "stages": [
                {
                    "name": "research",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://www.google.com/search?q=lead+generation"},
                        {"type": "SHELL_SAFE", "command": "echo identify buyer segments and pain points"},
                    ],
                    "metrics": ["traffic", "engagement"],
                    "success_criteria": {"validation_score_gte": 50},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "offer_test",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo draft offer + CTA variants"},
                        {"type": "METRIC_SET", "metrics": {"conversions": 0.0}},
                        {"type": "SHELL_SAFE", "command": "echo define lead quality proxy metrics"},
                    ],
                    "metrics": ["conversions", "engagement"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "WEB_GET", "url": "https://www.google.com/search?q=lead+generation"},
                {"type": "SHELL_SAFE", "command": "echo leadgen experiment simulated"},
            ],
            "metrics": ["traffic", "conversions", "engagement"],
            "rollback": {"strategy": "none"},
        },
        "content_growth": {
            "objective": "Validate content growth channels and engagement signals.",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["trend_probe", "distribution_loop"]},
            "stages": [
                {
                    "name": "trend_probe",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://trends.google.com"},
                        {"type": "SHELL_SAFE", "command": "echo generate topic clusters"},
                    ],
                    "metrics": ["traffic", "engagement"],
                    "success_criteria": {"validation_score_gte": 55},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "distribution_loop",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://www.reddit.com"},
                        {"type": "SHELL_SAFE", "command": "echo define distribution cadence"},
                        {"type": "METRIC_SET", "metrics": {"engagement": 1.0}},
                    ],
                    "metrics": ["engagement", "traffic"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "WEB_GET", "url": "https://trends.google.com"},
                {"type": "SHELL_SAFE", "command": "echo content growth probe"},
            ],
            "metrics": ["traffic", "engagement", "revenue_signals"],
            "rollback": {"strategy": "none"},
        },
        "market_demand_validation": {
            "objective": "Validate market demand by checking multi-source signals.",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["signals", "pmf_probe"]},
            "stages": [
                {
                    "name": "signals",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://www.reddit.com"},
                        {"type": "WEB_GET", "url": "https://api.github.com"},
                        {"type": "SHELL_SAFE", "command": "echo extract recurring pain points"},
                    ],
                    "metrics": ["traffic", "engagement"],
                    "success_criteria": {"validation_score_gte": 55},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "pmf_probe",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo define PMF survey questions + criteria"},
                        {"type": "METRIC_SET", "metrics": {"conversions": 0.0, "revenue_signals": 0.0}},
                    ],
                    "metrics": ["conversions", "revenue_signals", "engagement"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "WEB_GET", "url": "https://www.reddit.com"},
                {"type": "WEB_GET", "url": "https://api.github.com"},
                {"type": "SHELL_SAFE", "command": "echo market demand validation"},
            ],
            "metrics": ["traffic", "engagement"],
            "rollback": {"strategy": "none"},
        },
        "saas_prototype_experiment": {
            "objective": "Prototype a minimal SaaS concept and validate feasibility signals (safe workflow).",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["prototype_scope", "prototype_validate", "scale_decision"]},
            "stages": [
                {
                    "name": "prototype_scope",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo define problem statement"},
                        {"type": "SHELL_SAFE", "command": "echo draft PRD-lite"},
                        {"type": "SHELL_SAFE", "command": "echo define success metrics"},
                    ],
                    "metrics": ["engagement"],
                    "success_criteria": {"validation_score_gte": 50},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "prototype_validate",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://api.github.com"},
                        {"type": "SHELL_SAFE", "command": "echo validate feasibility constraints"},
                        {"type": "METRIC_SET", "metrics": {"revenue_signals": 0.0, "conversions": 0.0}},
                    ],
                    "metrics": ["traffic", "engagement", "revenue_signals", "conversions"],
                    "success_criteria": {"validation_score_gte": 65},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "scale_decision",
                    "lifecycle_status": "LIVE",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo decide scale vs iterate"},
                    ],
                    "metrics": ["validation_score"],
                    "success_criteria": {"validation_score_gte": 70},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "SHELL_SAFE", "command": "echo define problem statement"},
                {"type": "WEB_GET", "url": "https://api.github.com"},
                {"type": "SHELL_SAFE", "command": "echo sketch prototype scope"},
                {"type": "SHELL_SAFE", "command": "echo identify core user journey"},
            ],
            "metrics": ["engagement", "traffic", "revenue_signals"],
            "rollback": {"strategy": "none"},
        },
        "landing_page_validation": {
            "objective": "Validate landing page messaging and intent signals (safe workflow).",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["hypothesis", "conversion_test", "iterate_or_kill"]},
            "stages": [
                {
                    "name": "hypothesis",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo define hypothesis + ICP"},
                        {"type": "SHELL_SAFE", "command": "echo write value prop variants"},
                    ],
                    "metrics": ["engagement"],
                    "success_criteria": {"validation_score_gte": 50},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "conversion_test",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://news.ycombinator.com"},
                        # WEB_GET now returns structured HTML + metadata usable by playbooks.
                        {"type": "SHELL_SAFE", "command": "echo extract title/meta from WEB_GET output (manual in this phase)"},
                        {"type": "METRIC_SET", "metrics": {"traffic": 1.0, "conversions": 0.0}},
                        {"type": "SHELL_SAFE", "command": "echo evaluate CTA click proxy"},
                    ],
                    "metrics": ["traffic", "conversions", "engagement"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "iterate_or_kill",
                    "lifecycle_status": "LIVE",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo decide iterate vs terminate"},
                    ],
                    "metrics": ["validation_score"],
                    "success_criteria": {"validation_score_gte": 65},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "SHELL_SAFE", "command": "echo draft landing page hypothesis"},
                {"type": "WEB_GET", "url": "https://news.ycombinator.com"},
                {"type": "SHELL_SAFE", "command": "echo define CTA and measurement plan"},
            ],
            "metrics": ["traffic", "conversions", "engagement"],
            "rollback": {"strategy": "none"},
        },
        "marketing_funnel_test": {
            "objective": "Test a simple marketing funnel: acquisition → engagement → conversion proxy (safe workflow).",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["acquire", "activate", "convert"]},
            "stages": [
                {
                    "name": "acquire",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo pick acquisition channel"},
                        {"type": "WEB_GET", "url": "https://www.producthunt.com"},
                        {"type": "SHELL_SAFE", "command": "echo inspect WEB_GET html.title/html.meta for positioning clues"},
                        {"type": "METRIC_SET", "metrics": {"traffic": 1.0}},
                    ],
                    "metrics": ["traffic"],
                    "success_criteria": {"validation_score_gte": 50},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "activate",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo define activation event"},
                        {"type": "METRIC_SET", "metrics": {"engagement": 1.0}},
                    ],
                    "metrics": ["engagement"],
                    "success_criteria": {"validation_score_gte": 55},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "convert",
                    "lifecycle_status": "LIVE",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo define conversion proxy"},
                        {"type": "METRIC_SET", "metrics": {"conversions": 0.0, "revenue_signals": 0.0}},
                    ],
                    "metrics": ["conversions", "revenue_signals"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "SHELL_SAFE", "command": "echo pick acquisition channel"},
                {"type": "WEB_GET", "url": "https://www.producthunt.com"},
                {"type": "SHELL_SAFE", "command": "echo define engagement event"},
                {"type": "SHELL_SAFE", "command": "echo define conversion proxy"},
            ],
            "metrics": ["traffic", "engagement", "conversions", "revenue_signals"],
            "rollback": {"strategy": "none"},
        },
        "content_growth_loop": {
            "objective": "Validate a content growth loop via repeated signal checks and iteration (safe workflow).",
            "schema_version": 2,
            "lifecycle": {"stage_order": ["discover", "produce", "distribute", "iterate"]},
            "stages": [
                {
                    "name": "discover",
                    "lifecycle_status": "APPROVED",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://trends.google.com"},
                        {"type": "SHELL_SAFE", "command": "echo generate content angles"},
                    ],
                    "metrics": ["traffic", "engagement"],
                    "success_criteria": {"validation_score_gte": 50},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "produce",
                    "lifecycle_status": "TESTING",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo produce content draft checklist"},
                        {"type": "METRIC_SET", "metrics": {"engagement": 1.0}},
                    ],
                    "metrics": ["engagement"],
                    "success_criteria": {"validation_score_gte": 55},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "distribute",
                    "lifecycle_status": "LIVE",
                    "actions": [
                        {"type": "WEB_GET", "url": "https://www.reddit.com"},
                        {"type": "SHELL_SAFE", "command": "echo plan distribution loop"},
                        {"type": "METRIC_SET", "metrics": {"traffic": 1.0}},
                    ],
                    "metrics": ["traffic"],
                    "success_criteria": {"validation_score_gte": 60},
                    "rollback": {"strategy": "none"},
                },
                {
                    "name": "iterate",
                    "lifecycle_status": "SCALING",
                    "actions": [
                        {"type": "SHELL_SAFE", "command": "echo iterate based on engagement signals"},
                    ],
                    "metrics": ["validation_score"],
                    "success_criteria": {"validation_score_gte": 65},
                    "rollback": {"strategy": "none"},
                },
            ],
            "actions": [
                {"type": "WEB_GET", "url": "https://trends.google.com"},
                {"type": "SHELL_SAFE", "command": "echo generate content angles"},
                {"type": "WEB_GET", "url": "https://www.reddit.com"},
                {"type": "SHELL_SAFE", "command": "echo plan distribution loop"},
            ],
            "metrics": ["traffic", "engagement"],
            "rollback": {"strategy": "none"},
        },
    }


def get_playbook(name: str) -> Dict[str, Any] | None:
    return list_playbooks().get(name)

