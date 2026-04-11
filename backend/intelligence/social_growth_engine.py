from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from backend.database import get_db
from backend.intelligence.market_intelligence_engine import MarketIntelligenceEngine
from backend.system.audit_log import audit_log


class SocialGrowthEngine:
    """
    Human-assisted growth engine.
    Every outbound artifact is suggestion-only and approval-gated.
    """

    OWN_PLATFORMS = {"linkedin", "x", "instagram"}
    LISTEN_PLATFORMS = {"linkedin", "x", "reddit", "fiverr", "upwork"}
    VALID_INTENT = {"high", "medium", "low"}
    VALID_STATUS = {"pending_approval", "approved", "rejected", "published"}

    def __init__(self) -> None:
        self.market_engine = MarketIntelligenceEngine()

    # ------------------------
    # Section 1: market listening (read-only)
    # ------------------------

    def ingest_market_signals(self, *, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        stored: List[Dict[str, Any]] = []
        skipped = 0
        for item in signals:
            platform = str(item.get("platform") or "").strip().lower()
            content = str(item.get("text") or item.get("content") or "").strip()
            if platform not in self.LISTEN_PLATFORMS or not content:
                skipped += 1
                continue
            classified = self.market_engine.ingest_signal(
                platform=platform,
                content=content,
                source_url=str(item.get("source_url") or ""),
                author_handle=str(item.get("author") or item.get("author_handle") or ""),
                is_simulated=bool(item.get("is_simulated", False)),
            )
            if classified.get("event_id"):
                stored.append(classified)

        opportunities = self.market_engine.discover_opportunities(limit=max(1, len(stored)), real_only=False)
        return {
            "stored_signals": len(stored),
            "skipped": skipped,
            "opportunity_sync": opportunities,
            "mode": "read_only",
        }

    # ------------------------
    # Section 2+3: content intelligence + social manager
    # ------------------------

    def generate_content_suggestions(
        self,
        *,
        progress_update: str = "",
        limit: int = 6,
    ) -> Dict[str, Any]:
        demand = self._top_demand_signals(limit=max(2, int(limit)))
        templates = [
            ("problem", "Most teams lose deals because {pain}."),
            ("educational", "If you are facing {pain}, start with this workflow: {tip}."),
            ("build_in_public", "NOVA update: {progress}. What should we optimize next?"),
            ("contrarian", "Hot take: {pain} is not a traffic problem. It's a qualification problem."),
        ]
        suggestions = []
        for idx, signal in enumerate(demand):
            t = templates[idx % len(templates)]
            pain = signal.get("problem_summary") or "inconsistent lead flow"
            category = signal.get("category") or "marketing"
            body = t[1].format(
                pain=pain,
                tip=f"map {category} bottlenecks before buying more traffic",
                progress=progress_update or "we shipped a safer approval queue for outbound actions",
            )
            suggestions.append(
                {
                    "content_type": t[0],
                    "source_event_id": signal.get("id"),
                    "platform": "linkedin",
                    "hook": f"{category.replace('_', ' ').title()} signal: {pain[:70]}",
                    "body": body,
                    "cta": "If this sounds familiar, comment 'NOVA' and we'll share the playbook.",
                    "status": "pending_approval",
                }
            )

        created_ids = []
        with get_db() as conn:
            cursor = conn.cursor()
            for item in suggestions:
                cursor.execute(
                    """
                    INSERT INTO social_content_queue
                    (platform, content_type, hook, body, cta, source_event_id, status, scheduled_for)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending_approval', NULL)
                    """,
                    (
                        item["platform"],
                        item["content_type"],
                        item["hook"],
                        item["body"],
                        item["cta"],
                        int(item["source_event_id"] or 0) or None,
                    ),
                )
                created_ids.append(int(cursor.lastrowid))
            conn.commit()

        audit_log(actor="social_growth", action="content.suggested", target="batch", payload={"count": len(created_ids)})
        return {"created": len(created_ids), "content_ids": created_ids, "status": "pending_approval"}

    def queue_social_post(self, *, platform: str, content_type: str, hook: str, body: str, cta: str, scheduled_for: str = ""):
        p = str(platform).strip().lower()
        if p not in self.OWN_PLATFORMS:
            return {"error": "unsupported_platform"}

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO social_content_queue
                (platform, content_type, hook, body, cta, status, scheduled_for)
                VALUES (?, ?, ?, ?, ?, 'pending_approval', ?)
                """,
                (p, str(content_type), str(hook), str(body), str(cta), str(scheduled_for or "") or None),
            )
            content_id = int(cursor.lastrowid)
            conn.commit()

        return {"content_id": content_id, "status": "pending_approval"}

    # ------------------------
    # Section 4+5+6: engagement, reply suggestions, lead detection
    # ------------------------

    def ingest_engagement(self, *, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        stored = 0
        suggested = 0
        detected_leads = 0

        with get_db() as conn:
            cursor = conn.cursor()
            for item in events:
                platform = str(item.get("platform") or "").strip().lower()
                if platform not in self.OWN_PLATFORMS:
                    continue

                message = str(item.get("message") or item.get("text") or "").strip()
                username = str(item.get("username") or item.get("handle") or "unknown")
                if not message:
                    continue

                intent = self._classify_intent(message)
                cursor.execute(
                    """
                    INSERT INTO social_engagement_events
                    (platform, username, event_type, message, intent_level, intent_score, context_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        platform,
                        username,
                        str(item.get("event_type") or "comment"),
                        message,
                        intent["intent_level"],
                        intent["intent_score"],
                        json.dumps({"post_id": item.get("post_id"), "thread_id": item.get("thread_id")}),
                    ),
                )
                event_id = int(cursor.lastrowid)
                stored += 1

                if intent["intent_level"] in {"high", "medium"}:
                    reply = self._build_reply_suggestion(platform=platform, message=message, intent=intent["intent_level"])
                    cursor.execute(
                        """
                        INSERT INTO social_reply_queue
                        (engagement_event_id, platform, username, message_type, suggestion, status)
                        VALUES (?, ?, ?, 'comment_reply', ?, 'pending_approval')
                        """,
                        (event_id, platform, username, reply),
                    )
                    suggested += 1

                if intent["intent_level"] == "high":
                    cursor.execute(
                        """
                        INSERT INTO social_leads
                        (platform, username, lead_profile, intent_level, intent_score, source_event_id, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'new')
                        """,
                        (
                            platform,
                            username,
                            json.dumps({"summary": message[:200], "captured_at": datetime.utcnow().isoformat()}),
                            intent["intent_level"],
                            intent["intent_score"],
                            event_id,
                        ),
                    )
                    detected_leads += 1
            conn.commit()

        return {"stored_engagement": stored, "suggested_replies": suggested, "detected_leads": detected_leads}

    def suggest_dm(self, *, lead_id: int, context: str = "") -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, platform, username, intent_level FROM social_leads WHERE id=?", (int(lead_id),))
            lead = cursor.fetchone()
            if not lead:
                return {"error": "lead_not_found"}

            msg = (
                f"Hey @{lead['username']} — appreciate your question. "
                f"If useful, I can share a short plan for {context or 'your growth bottleneck'} and keep it practical."
            )
            cursor.execute(
                """
                INSERT INTO social_reply_queue
                (lead_id, platform, username, message_type, suggestion, status)
                VALUES (?, ?, ?, 'dm_suggestion', ?, 'pending_approval')
                """,
                (int(lead["id"]), str(lead["platform"]), str(lead["username"]), msg),
            )
            queue_id = int(cursor.lastrowid)
            conn.commit()

        return {"queue_id": queue_id, "status": "pending_approval", "suggestion": msg}

    # ------------------------
    # Section 7+8: approval + admin console
    # ------------------------

    def update_content_status(self, *, content_id: int, status: str, admin_user: str) -> Dict[str, Any]:
        normalized = str(status).strip().lower()
        if normalized not in self.VALID_STATUS:
            return {"error": "invalid_status"}

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE social_content_queue
                SET status=?, reviewed_by=?, reviewed_at=datetime('now')
                WHERE id=?
                """,
                (normalized, str(admin_user), int(content_id)),
            )
            ok = cursor.rowcount > 0
            conn.commit()
        return {"content_id": int(content_id), "updated": bool(ok), "status": normalized}

    def update_reply_status(self, *, queue_id: int, status: str, admin_user: str) -> Dict[str, Any]:
        normalized = str(status).strip().lower()
        if normalized not in self.VALID_STATUS:
            return {"error": "invalid_status"}

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE social_reply_queue
                SET status=?, reviewed_by=?, reviewed_at=datetime('now')
                WHERE id=?
                """,
                (normalized, str(admin_user), int(queue_id)),
            )
            ok = cursor.rowcount > 0
            conn.commit()
        return {"queue_id": int(queue_id), "updated": bool(ok), "status": normalized}

    def get_console_snapshot(self) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM social_content_queue WHERE status='pending_approval' ORDER BY id DESC LIMIT 50")
            pending_posts = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM social_reply_queue WHERE status='pending_approval' ORDER BY id DESC LIMIT 50")
            pending_replies = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM social_leads ORDER BY id DESC LIMIT 100")
            leads = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT platform, COUNT(*) AS posts, SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) AS published
                FROM social_content_queue GROUP BY platform
                """
            )
            performance = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT action, details, created_at FROM social_activity_log ORDER BY id DESC LIMIT 200")
            activity = [dict(r) for r in cursor.fetchall()]

        return {
            "pending_posts": pending_posts,
            "pending_replies": pending_replies,
            "detected_leads": leads,
            "activity_logs": activity,
            "platform_performance": performance,
            "compliance": {
                "human_in_loop": True,
                "auto_posting": False,
                "auto_dm": False,
                "spam_automation": False,
            },
        }

    def append_activity(self, *, action: str, details: Dict[str, Any] | None = None) -> None:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO social_activity_log (action, details) VALUES (?, ?)",
                (str(action), json.dumps(details or {})),
            )
            conn.commit()

    def _classify_intent(self, text: str) -> Dict[str, Any]:
        t = str(text or "").lower()
        high_terms = ["need", "looking for", "hire", "budget", "asap", "urgent", "dm me"]
        med_terms = ["struggling", "how do i", "advice", "help", "problem", "issue"]

        score = 0.1
        for w in high_terms:
            if w in t:
                score += 0.2
        for w in med_terms:
            if w in t:
                score += 0.1

        score = max(0.0, min(1.0, score))
        level = "high" if score >= 0.75 else ("medium" if score >= 0.4 else "low")
        return {"intent_level": level, "intent_score": round(score, 3)}

    def _build_reply_suggestion(self, *, platform: str, message: str, intent: str) -> str:
        if intent == "high":
            return (
                "Thanks for sharing this — happy to help. "
                "If useful, I can send a concise action plan and timeline for your specific goal."
            )
        return (
            "Great question. A practical next step is to diagnose the bottleneck first "
            "(traffic, conversion, or follow-up), then pick one focused experiment."
        )

    def _top_demand_signals(self, *, limit: int = 6) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, category, problem_summary, intent_level, urgency_score
                FROM market_intelligence_events
                ORDER BY intent_score DESC, urgency_score DESC, id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = [dict(r) for r in cursor.fetchall()]

        if rows:
            return rows

        # fallback deterministic seed if no market events exist yet
        defaults = [
            "founders struggling with inconsistent inbound leads",
            "teams needing website conversion fixes",
            "operators asking for workflow automation",
        ]
        synthetic = []
        for idx, text in enumerate(defaults, start=1):
            synthetic.append({"id": idx, "category": "marketing", "problem_summary": text, "intent_level": "medium", "urgency_score": 0.5})
        return synthetic[:limit]
