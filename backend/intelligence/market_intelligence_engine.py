from __future__ import annotations

import json
from typing import Any, Dict, List

from backend.database import get_db
from backend.system.audit_log import audit_log


class MarketIntelligenceEngine:
    """
    Collects and classifies market signals (real/simulated separated),
    extracting intent, urgency, and category for opportunity discovery.
    """

    ALLOWED_PLATFORMS = {"linkedin", "x", "reddit", "fiverr", "upwork"}

    def ingest_signal(
        self,
        *,
        platform: str,
        content: str,
        source_url: str = "",
        author_handle: str = "",
        is_simulated: bool = False,
    ) -> Dict[str, Any]:
        p = str(platform).strip().lower()
        if p not in self.ALLOWED_PLATFORMS:
            return {"error": "unsupported_platform", "platform": p}

        classification = self._classify(content)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO market_intelligence_events
                (platform, source_url, author_handle, content, intent_level, intent_score, category, urgency_score, problem_summary, is_simulated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    p,
                    str(source_url or ""),
                    str(author_handle or ""),
                    str(content or ""),
                    classification["intent_level"],
                    float(classification["intent_score"]),
                    classification["category"],
                    float(classification["urgency_score"]),
                    classification["problem_summary"],
                    1 if is_simulated else 0,
                ),
            )
            event_id = int(cursor.lastrowid)
            conn.commit()

        audit_log(actor="market_intelligence", action="signal.ingested", target=str(event_id), payload={"platform": p, **classification})
        return {"event_id": event_id, "platform": p, **classification}

    def discover_opportunities(self, *, limit: int = 50, real_only: bool = True) -> Dict[str, Any]:
        where = "WHERE 1=1"
        params: List[Any] = []
        if real_only:
            where += " AND is_simulated=0"

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, platform, source_url, author_handle, intent_level, intent_score, category, urgency_score, problem_summary, content
                FROM market_intelligence_events
                {where}
                ORDER BY (intent_score*0.6 + urgency_score*0.4) DESC, id DESC
                LIMIT ?
                """,
                tuple(params + [int(limit)]),
            )
            rows = cursor.fetchall()

            created = 0
            opportunities: List[Dict[str, Any]] = []
            for row in rows:
                confidence = round((float(row["intent_score"] or 0.0) * 0.7) + (float(row["urgency_score"] or 0.0) * 0.3), 4)
                cursor.execute(
                    """
                    INSERT INTO opportunities
                    (market_event_id, platform, category, intent_level, intent_score, urgency_score, confidence_score, problem_statement, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'NEW')
                    """,
                    (
                        int(row["id"]),
                        str(row["platform"]),
                        str(row["category"]),
                        str(row["intent_level"]),
                        float(row["intent_score"]),
                        float(row["urgency_score"]),
                        confidence,
                        str(row["problem_summary"]),
                    ),
                )
                opp_id = int(cursor.lastrowid)
                opportunities.append(
                    {
                        "opportunity_id": opp_id,
                        "event_id": int(row["id"]),
                        "platform": str(row["platform"]),
                        "category": str(row["category"]),
                        "intent_level": str(row["intent_level"]),
                        "confidence_score": confidence,
                    }
                )
                created += 1
            conn.commit()

        return {"created_opportunities": created, "opportunities": opportunities}

    def _classify(self, text: str) -> Dict[str, Any]:
        t = str(text or "").lower()

        website_words = ["website", "landing page", "web design", "site"]
        lead_words = ["lead", "appointment", "clients", "inbound", "outreach"]
        automation_words = ["automation", "workflow", "zapier", "crm", "integration"]

        buy_words = ["need", "looking for", "hire", "ready to", "budget"]
        urgent_words = ["asap", "urgent", "today", "this week", "immediately"]

        score = 0.1
        for w in buy_words:
            if w in t:
                score += 0.2
        urgency = 0.05
        for w in urgent_words:
            if w in t:
                urgency += 0.2

        category = "lead_generation"
        if any(w in t for w in website_words):
            category = "website_development"
        elif any(w in t for w in automation_words):
            category = "automation"
        elif any(w in t for w in lead_words):
            category = "lead_generation"

        score = max(0.0, min(1.0, score))
        urgency = max(0.0, min(1.0, urgency))
        intent_level = "high" if score >= 0.7 else ("medium" if score >= 0.35 else "low")

        summary = text[:180].strip() if text else "unspecified market problem"
        return {
            "intent_level": intent_level,
            "intent_score": round(score, 4),
            "urgency_score": round(urgency, 4),
            "category": category,
            "problem_summary": summary,
        }
