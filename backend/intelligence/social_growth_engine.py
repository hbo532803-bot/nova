from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from backend.database import get_db
from backend.intelligence.market_intelligence_engine import MarketIntelligenceEngine
from backend.intelligence.offer_conversion_engine import OfferConversionEngine
from backend.knowledge.graph_store import KnowledgeGraphStore
from backend.system.audit_log import audit_log


class SocialGrowthEngine:
    """
    Human-assisted social + revenue engine.
    Outbound actions are still approval gated, but each qualified lead is now
    connected to a concrete offer + conversion pipeline.
    """

    OWN_PLATFORMS = {"linkedin", "x", "instagram"}
    LISTEN_PLATFORMS = {"linkedin", "x", "reddit", "fiverr", "upwork"}
    VALID_STATUS = {"pending_approval", "approved", "rejected", "published", "sent"}

    def __init__(self) -> None:
        self.market_engine = MarketIntelligenceEngine()
        self.offer_engine = OfferConversionEngine()
        self.graph = KnowledgeGraphStore()

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
        return {"stored_signals": len(stored), "skipped": skipped, "opportunity_sync": opportunities, "mode": "read_only"}

    # ------------------------
    # Section 2+3+5: content intelligence + manager + feedback loop
    # ------------------------

    def generate_content_suggestions(self, *, progress_update: str = "", limit: int = 6) -> Dict[str, Any]:
        demand = self._top_demand_signals(limit=max(2, int(limit)))
        best_patterns = self._best_content_patterns(limit=2)

        suggestions: List[Dict[str, Any]] = []
        for idx, signal in enumerate(demand):
            category = signal.get("category") or "marketing"
            pain = signal.get("problem_summary") or "inconsistent lead flow"
            pattern_hint = ""
            if best_patterns:
                top = best_patterns[idx % len(best_patterns)]
                pattern_hint = f" Pattern hint: posts like {top.get('post_id', 'top performers')} converted best."

            content_type = ["problem", "educational", "build_in_public", "contrarian"][idx % 4]
            hook = f"{category.replace('_', ' ').title()} bottleneck: {pain[:70]}"
            body = (
                f"We keep seeing this issue: {pain}. "
                f"NOVA now maps demand signals directly to offer flows so teams can turn engagement into qualified pipeline.{pattern_hint} "
                f"Build update: {progress_update or 'we connected social leads to offer + conversion tracking.'}"
            )
            cta = "If this is your bottleneck, reply 'audit' and I can share the exact fix path."
            suggestions.append(
                {
                    "content_type": content_type,
                    "source_event_id": signal.get("id"),
                    "platform": "linkedin",
                    "hook": hook,
                    "body": body,
                    "cta": cta,
                    "status": "pending_approval",
                }
            )

        ids: List[int] = []
        with get_db() as conn:
            cursor = conn.cursor()
            for item in suggestions:
                cursor.execute(
                    """
                    INSERT INTO social_content_queue
                    (platform, content_type, hook, body, cta, source_event_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending_approval')
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
                ids.append(int(cursor.lastrowid))
            conn.commit()

        self.append_activity(action="content_suggestions_generated", details={"count": len(ids)})
        return {"created": len(ids), "content_ids": ids, "status": "pending_approval"}

    def queue_social_post(self, *, platform: str, content_type: str, hook: str, body: str, cta: str, scheduled_for: str = "") -> Dict[str, Any]:
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
    # Section 1+2+3+6: engagement -> lead -> offer -> conversion queue
    # ------------------------

    def ingest_engagement(self, *, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        stored = 0
        suggested = 0
        detected_leads = 0
        offers_generated = 0

        with get_db() as conn:
            cursor = conn.cursor()
            for item in events:
                platform = str(item.get("platform") or "").strip().lower()
                if platform not in self.OWN_PLATFORMS:
                    continue

                message = str(item.get("message") or item.get("text") or "").strip()
                username = str(item.get("username") or item.get("handle") or "unknown")
                post_id = str(item.get("post_id") or "")
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
                        json.dumps({"post_id": post_id, "thread_id": item.get("thread_id")}),
                    ),
                )
                event_id = int(cursor.lastrowid)
                stored += 1

                if intent["intent_level"] in {"high", "medium"}:
                    flow = self._create_revenue_flow(
                        username=username,
                        platform=platform,
                        message=message,
                        post_id=post_id,
                        intent_level=intent["intent_level"],
                        intent_score=float(intent["intent_score"]),
                        social_event_id=event_id,
                    )
                    detected_leads += 1
                    if flow.get("attempt_id"):
                        offers_generated += 1

                    reply = self._build_conversion_reply(
                        message=message,
                        offer=flow.get("offer") or {},
                        username=username,
                    )
                    cursor.execute(
                        """
                        INSERT INTO social_reply_queue
                        (engagement_event_id, lead_id, platform, username, message_type, suggestion, status)
                        VALUES (?, ?, ?, ?, 'comment_reply', ?, 'pending_approval')
                        """,
                        (
                            int(event_id),
                            int(flow.get("social_lead_id") or 0) or None,
                            platform,
                            username,
                            reply,
                        ),
                    )
                    suggested += 1

                    self._track_social_roi(
                        platform=platform,
                        post_id=post_id,
                        lead_delta=1,
                        conversion_delta=0,
                        revenue_delta=0.0,
                    )
            conn.commit()

        return {
            "stored_engagement": stored,
            "suggested_replies": suggested,
            "detected_leads": detected_leads,
            "offers_generated": offers_generated,
        }

    def suggest_dm(self, *, lead_id: int, context: str = "") -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT l.id, l.platform, l.username, p.conversion_attempt_id
                FROM social_leads l
                LEFT JOIN social_conversion_pipeline p ON p.social_lead_id=l.id
                WHERE l.id=?
                ORDER BY p.id DESC LIMIT 1
                """,
                (int(lead_id),),
            )
            row = cursor.fetchone()
            if not row:
                return {"error": "lead_not_found"}

            offer = self._attempt_offer(int(row["conversion_attempt_id"] or 0)) if row["conversion_attempt_id"] else {}
            dm = self._build_conversion_dm(username=str(row["username"]), context=context, offer=offer)
            cursor.execute(
                """
                INSERT INTO social_reply_queue
                (lead_id, platform, username, message_type, suggestion, status)
                VALUES (?, ?, ?, 'dm_suggestion', ?, 'pending_approval')
                """,
                (int(row["id"]), str(row["platform"]), str(row["username"]), dm),
            )
            queue_id = int(cursor.lastrowid)
            conn.commit()

        return {"queue_id": queue_id, "status": "pending_approval", "suggestion": dm}

    def mark_reply_sent(self, *, queue_id: int, admin_user: str) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE social_reply_queue SET status='sent', reviewed_by=?, reviewed_at=datetime('now') WHERE id=?",
                (str(admin_user), int(queue_id)),
            )
            ok = cursor.rowcount > 0
            conn.commit()
        return {"queue_id": int(queue_id), "sent": bool(ok)}

    def mark_conversion(
        self,
        *,
        social_lead_id: int,
        amount: float,
        admin_user: str,
        response_state: str = "accepted",
    ) -> Dict[str, Any]:
        pipeline = self._pipeline_for_social_lead(int(social_lead_id))
        if not pipeline:
            return {"error": "pipeline_not_found"}
        if float(amount) <= 0:
            return {"error": "invalid_amount"}

        payment = self.offer_engine.mark_real_payment(
            attempt_id=int(pipeline.get("conversion_attempt_id") or 0),
            amount=float(amount),
            approved_by=str(admin_user),
        )
        if payment.get("error"):
            return payment

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE social_conversion_pipeline
                SET status='converted', response_state=?, revenue_amount=?, converted_at=datetime('now')
                WHERE id=?
                """,
                (str(response_state), float(amount), int(pipeline["id"])),
            )
            cursor.execute(
                "UPDATE social_leads SET status='converted' WHERE id=?",
                (int(social_lead_id),),
            )
            conn.commit()

        self._track_social_roi(
            platform=str(pipeline.get("platform") or "unknown"),
            post_id=str(pipeline.get("post_id") or ""),
            lead_delta=0,
            conversion_delta=1,
            revenue_delta=float(amount),
        )

        self.graph.add_edge("social_lead", str(social_lead_id), "converted_to", "revenue_event", str(payment.get("attempt_id")))
        return {"social_lead_id": int(social_lead_id), "amount": float(amount), "status": "converted", "payment": payment}

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
                "UPDATE social_content_queue SET status=?, reviewed_by=?, reviewed_at=datetime('now') WHERE id=?",
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
                "UPDATE social_reply_queue SET status=?, reviewed_by=?, reviewed_at=datetime('now') WHERE id=?",
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

            cursor.execute(
                """
                SELECT l.*, p.conversion_attempt_id, p.status AS pipeline_status, p.revenue_amount, p.post_id
                FROM social_leads l
                LEFT JOIN social_conversion_pipeline p ON p.social_lead_id=l.id
                ORDER BY l.id DESC
                LIMIT 100
                """
            )
            leads = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT platform,
                       COUNT(*) AS posts,
                       SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) AS published
                FROM social_content_queue
                GROUP BY platform
                """
            )
            performance = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT REPLACE(source, 'social_growth_engine:', '') AS platform,
                       SUM(CASE WHEN metric_key LIKE 'social_post:%:leads' THEN metric_value ELSE 0 END) AS leads,
                       SUM(CASE WHEN metric_key LIKE 'social_post:%:conversions' THEN metric_value ELSE 0 END) AS conversions,
                       SUM(CASE WHEN metric_key='social_revenue' THEN metric_value ELSE 0 END) AS revenue
                FROM experiment_metrics
                WHERE source LIKE 'social_growth_engine:%'
                GROUP BY platform
                """
            )
            roi = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT action, details, created_at FROM social_activity_log ORDER BY id DESC LIMIT 200")
            activity = [dict(r) for r in cursor.fetchall()]

        return {
            "pending_posts": pending_posts,
            "pending_replies": pending_replies,
            "detected_leads": leads,
            "activity_logs": activity,
            "platform_performance": performance,
            "social_roi": roi,
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
            cursor.execute("INSERT INTO social_activity_log (action, details) VALUES (?, ?)", (str(action), json.dumps(details or {})))
            conn.commit()

    # ------------------------
    # Internal helpers
    # ------------------------

    def _create_revenue_flow(
        self,
        *,
        username: str,
        platform: str,
        message: str,
        post_id: str,
        intent_level: str,
        intent_score: float,
        social_event_id: int,
    ) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO leads (mission_id, name, source, intent_level, intent_score, approved_for_contact, last_interaction_source)
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    f"social-{platform}",
                    username,
                    f"{platform}_social",
                    intent_level,
                    float(intent_score),
                    platform,
                ),
            )
            lead_id = int(cursor.lastrowid)
            cursor.execute(
                """
                INSERT INTO social_leads (platform, username, lead_profile, intent_level, intent_score, source_event_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'new')
                """,
                (
                    platform,
                    username,
                    json.dumps({"summary": message[:240], "captured_at": datetime.utcnow().isoformat(), "post_id": post_id}),
                    intent_level,
                    float(intent_score),
                    int(social_event_id),
                ),
            )
            social_lead_id = int(cursor.lastrowid)
            conn.commit()

        service_type = self._service_from_message(message)
        offer = self.offer_engine.create_offer_for_lead(lead_id=lead_id, service_type=service_type, context={"channel": platform, "post_id": post_id})
        attempt_id = int(offer.get("attempt_id") or 0) if offer and not offer.get("error") else 0

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO social_conversion_pipeline
                (social_lead_id, lead_id, conversion_attempt_id, post_id, platform, status, response_state)
                VALUES (?, ?, ?, ?, ?, 'offer_generated', 'pending')
                """,
                (
                    int(social_lead_id),
                    int(lead_id),
                    attempt_id if attempt_id else None,
                    str(post_id or ""),
                    platform,
                ),
            )
            conn.commit()

        self.graph.upsert_node("social_lead", str(social_lead_id), {"platform": platform, "username": username, "intent": intent_level})
        self.graph.add_edge("social_lead", str(social_lead_id), "maps_to", "crm_lead", str(lead_id))
        if attempt_id:
            self.graph.add_edge("crm_lead", str(lead_id), "has_offer", "conversion_attempt", str(attempt_id))

        return {
            "social_lead_id": social_lead_id,
            "lead_id": lead_id,
            "attempt_id": attempt_id,
            "offer": offer.get("offer") if isinstance(offer, dict) else {},
        }

    def _track_social_roi(self, *, platform: str, post_id: str, lead_delta: int, conversion_delta: int, revenue_delta: float) -> None:
        pid = post_id or "unknown"
        with get_db() as conn:
            cursor = conn.cursor()
            if lead_delta:
                cursor.execute(
                    "INSERT INTO experiment_metrics (experiment_id, metric_key, metric_value, source, created_at) VALUES (NULL, ?, ?, ?, datetime('now'))",
                    (f"social_post:{pid}:leads", float(lead_delta), f"social_growth_engine:{platform}"),
                )
            if conversion_delta:
                cursor.execute(
                    "INSERT INTO experiment_metrics (experiment_id, metric_key, metric_value, source, created_at) VALUES (NULL, ?, ?, ?, datetime('now'))",
                    (f"social_post:{pid}:conversions", float(conversion_delta), f"social_growth_engine:{platform}"),
                )
            if revenue_delta:
                cursor.execute(
                    "INSERT INTO experiment_metrics (experiment_id, metric_key, metric_value, source, created_at) VALUES (NULL, 'social_revenue', ?, ?, datetime('now'))",
                    (float(revenue_delta), f"social_growth_engine:{platform}"),
                )
            conn.commit()

        self.graph.upsert_node("social_post", pid, {"platform": platform})
        self.graph.upsert_node("platform", platform, {"source": "social"})
        self.graph.add_edge("social_post", pid, "published_on", "platform", platform)

    def _classify_intent(self, text: str) -> Dict[str, Any]:
        t = str(text or "").lower()
        high_terms = ["need", "looking for", "hire", "budget", "asap", "urgent", "dm me"]
        med_terms = ["struggling", "how do i", "advice", "help", "problem", "issue"]
        score = 0.1
        score += sum(0.2 for w in high_terms if w in t)
        score += sum(0.1 for w in med_terms if w in t)
        score = max(0.0, min(1.0, score))
        level = "high" if score >= 0.75 else ("medium" if score >= 0.4 else "low")
        return {"intent_level": level, "intent_score": round(score, 3)}

    def _service_from_message(self, text: str) -> str:
        t = str(text or "").lower()
        if any(k in t for k in ["website", "landing", "site"]):
            return "website_development"
        if any(k in t for k in ["automation", "workflow", "crm"]):
            return "automation"
        return "lead_generation"

    def _build_conversion_reply(self, *, message: str, offer: Dict[str, Any], username: str) -> str:
        problem = message[:90]
        service = str(offer.get("service_type") or "growth system").replace("_", " ")
        tier = str(offer.get("tier") or "standard").upper()
        price = ((offer.get("pricing") or {}).get("final_price")) if isinstance(offer, dict) else None
        price_hint = f" ({tier} @ ${price})" if price else f" ({tier})"
        return (
            f"Thanks @{username} — I saw you mentioned: '{problem}'. "
            f"You're not alone; this is usually a funnel + follow-up issue. "
            f"I recently built a {service}{price_hint} offer that solves this with clear deliverables. "
            "Want me to share the exact plan?"
        )

    def _build_conversion_dm(self, *, username: str, context: str, offer: Dict[str, Any]) -> str:
        service = str(offer.get("service_type") or "growth pipeline").replace("_", " ")
        tier = str(offer.get("tier") or "standard").upper()
        price = ((offer.get("pricing") or {}).get("final_price")) if isinstance(offer, dict) else None
        return (
            f"Hey @{username}, appreciate the discussion. Based on your context ({context or 'lead flow bottleneck'}), "
            f"I can send a concise {service} plan in {tier} tier"
            f"{f' priced around ${price}' if price else ''}. No pressure—want me to send it?"
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
        return [
            {"id": 1, "category": "lead_generation", "problem_summary": "founders struggling with inconsistent inbound leads", "intent_level": "medium", "urgency_score": 0.5},
            {"id": 2, "category": "website_development", "problem_summary": "teams needing website conversion fixes", "intent_level": "medium", "urgency_score": 0.5},
        ][:limit]

    def _best_content_patterns(self, *, limit: int = 3) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    REPLACE(REPLACE(metric_key, 'social_post:', ''), ':conversions', '') AS post_id,
                    SUM(metric_value) AS conversions
                FROM experiment_metrics
                WHERE metric_key LIKE 'social_post:%:conversions'
                GROUP BY post_id
                ORDER BY conversions DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            return [dict(r) for r in cursor.fetchall()]

    def _pipeline_for_social_lead(self, social_lead_id: int) -> Dict[str, Any] | None:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM social_conversion_pipeline WHERE social_lead_id=? ORDER BY id DESC LIMIT 1", (int(social_lead_id),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _attempt_offer(self, attempt_id: int) -> Dict[str, Any]:
        if attempt_id <= 0:
            return {}
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT offer_payload_json FROM conversion_attempts WHERE id=?", (int(attempt_id),))
            row = cursor.fetchone()
        if not row:
            return {}
        try:
            return json.loads(str(row["offer_payload_json"] or "{}"))
        except Exception:
            return {}
