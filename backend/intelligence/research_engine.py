from __future__ import annotations

import datetime
import re
import json
from collections import Counter
from typing import Any, Dict, List

from backend.database import get_db
from backend.frontend_api.event_bus import broadcast
from backend.tools.web_access import safe_get
from backend.tools.tool_sandbox import ToolSandbox
from backend.knowledge.graph_store import KnowledgeGraphStore


class ResearchEngine:
    """
    Autonomous research pipeline (best-effort, safe):
    - topic discovery from a small set of allowlisted sources
    - signal extraction from structured WEB_GET output
    - lightweight trend/keyword scoring
    - opportunity hypothesis generation -> stored as market_proposals
    """

    SOURCES = [
        ("hn", "https://news.ycombinator.com/"),
        ("ph", "https://www.producthunt.com/"),
        ("reddit", "https://www.reddit.com/"),
    ]

    def __init__(self):
        self.sandbox = ToolSandbox(timeout_sec=5)
        self.kg = KnowledgeGraphStore()

    def run(self, *, max_proposals: int = 5) -> Dict[str, Any]:
        week_tag = self._current_week()
        texts: List[str] = []
        docs: List[Dict[str, Any]] = []
        fetched = []

        for name, url in self.SOURCES:
            out = self.sandbox.run(safe_get, url)
            fetched.append({"source": name, "url": url, "ok": bool(out.get("ok"))})
            if out.get("ok") and out.get("html", {}).get("text"):
                t = str(out["html"]["text"])
                texts.append(t)
                docs.append({"source": name, "url": url, "text": t, "links": out.get("html", {}).get("links") or []})

        clusters = self._cluster_docs(docs)
        problems = self._detect_problems("\n".join(texts))
        competitors = self._competitor_domains(docs)
        hypotheses = self._hypotheses(clusters, problems, competitors, max_proposals=max_proposals)
        stored = self._store_hypotheses(week_tag, hypotheses)

        payload = {
            "ok": True,
            "week_tag": week_tag,
            "fetched": fetched,
            "clusters": clusters,
            "problems": problems[:20],
            "competitors": competitors[:20],
            "proposals": stored,
        }
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                    ("research_last", json.dumps(payload)),
                )
                conn.commit()
        except Exception:
            pass

        broadcast({"type": "log", "level": "info", "message": f"ResearchEngine stored {len(stored)} proposals"})
        return payload

    def _current_week(self) -> str:
        today = datetime.date.today()
        return f"{today.year}-W{today.isocalendar()[1]}"

    def _keywords(self, text: str) -> List[tuple[str, int]]:
        # Simple tokenization; keep it conservative.
        tokens = [t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_\\-]{2,}", text)]
        stop = {
            "the",
            "and",
            "for",
            "you",
            "with",
            "that",
            "this",
            "from",
            "are",
            "was",
            "not",
            "your",
            "have",
            "will",
            "new",
            "all",
            "more",
            "about",
            "just",
            "what",
            "when",
            "how",
        }
        filtered = [t for t in tokens if t not in stop and len(t) <= 32]
        return Counter(filtered).most_common(50)

    def _to_proposals(self, keywords: List[tuple[str, int]], *, max_proposals: int) -> List[Dict[str, Any]]:
        out = []
        for kw, c in keywords[: max_proposals * 2]:
            cash_score = max(10.0, min(95.0, float(c) * 8.0))
            budget = max(50.0, min(500.0, float(c) * 25.0))
            out.append({"niche_name": f"{kw} tools", "cash_score": cash_score, "proposed_budget": budget})
            if len(out) >= max_proposals:
                break
        return out

    def _cluster_docs(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Lightweight semantic clustering: groups docs by top keywords overlap.
        """
        clusters: List[Dict[str, Any]] = []
        for d in docs:
            kws = {k for k, _ in self._keywords(d.get("text") or "")[:12]}
            placed = False
            for c in clusters:
                if len(kws & set(c["keywords"])) >= 3:
                    c["docs"].append({"source": d["source"], "url": d["url"]})
                    c["keywords"] = list(sorted(set(c["keywords"]) | kws))[:20]
                    placed = True
                    break
            if not placed:
                clusters.append({"keywords": list(sorted(kws))[:20], "docs": [{"source": d["source"], "url": d["url"]}]})
        return clusters

    def _detect_problems(self, text: str) -> List[str]:
        patterns = [
            r"\bproblem\b",
            r"\bpain\b",
            r"\bstruggle\b",
            r"\bfrustrat\w+\b",
            r"\bneed\b",
            r"\bcostly\b",
        ]
        lines = [l.strip() for l in re.split(r"[\\n\\.]+", text) if l.strip()]
        hits = []
        for ln in lines:
            low = ln.lower()
            if any(re.search(p, low) for p in patterns) and len(ln) > 20:
                hits.append(ln[:200])
            if len(hits) >= 50:
                break
        return hits

    def _competitor_domains(self, docs: List[Dict[str, Any]]) -> List[str]:
        from urllib.parse import urlparse

        domains = []
        for d in docs:
            for l in d.get("links") or []:
                try:
                    netloc = urlparse(str(l)).netloc.lower()
                    if netloc and "." in netloc and "ycombinator" not in netloc and "reddit" not in netloc:
                        domains.append(netloc)
                except Exception:
                    continue
        return [d for d, _ in Counter(domains).most_common(50)]

    def _hypotheses(
        self,
        clusters: List[Dict[str, Any]],
        problems: List[str],
        competitors: List[str],
        *,
        max_proposals: int,
    ) -> List[Dict[str, Any]]:
        out = []
        for c in clusters[: max_proposals]:
            kw = (c.get("keywords") or ["tools"])[0]
            niche = f"{kw} workflow"
            cash_score = 60.0
            budget = 150.0
            out.append(
                {
                    "niche_name": niche,
                    "cash_score": cash_score,
                    "proposed_budget": budget,
                    "hypothesis": {
                        "cluster_keywords": c.get("keywords") or [],
                        "problem_signals": problems[:5],
                        "competitors": competitors[:5],
                        "recommended_playbook": "landing_page_validation",
                    },
                }
            )
        if not out:
            out = [{"niche_name": "market workflow", "cash_score": 50.0, "proposed_budget": 100.0, "hypothesis": {}}]
        return out[:max_proposals]

    def _store_hypotheses(self, week_tag: str, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stored: List[Dict[str, Any]] = []
        with get_db() as conn:
            cursor = conn.cursor()
            for p in hypotheses:
                cursor.execute(
                    """
                    INSERT INTO market_proposals (niche_name, week_tag, cash_score, proposed_budget, status)
                    VALUES (?, ?, ?, ?, 'PENDING')
                    """,
                    (p["niche_name"], week_tag, float(p["cash_score"]), float(p["proposed_budget"])),
                )
                pid = cursor.lastrowid
                stored.append({"id": pid, "niche_name": p["niche_name"], "cash_score": p["cash_score"], "proposed_budget": p["proposed_budget"], "week_tag": week_tag, "status": "PENDING"})
                # Store structured hypothesis in system_settings
                cursor.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                    (f"proposal_hypothesis_{pid}", json.dumps(p.get("hypothesis") or {})),
                )
            conn.commit()

        # Knowledge graph: proposals become opportunity nodes
        for s in stored:
            try:
                self.kg.upsert_node("opportunity", str(s["id"]), s)
                self.kg.add_edge("strategy", "current", "DISCOVERED", "opportunity", str(s["id"]))
            except Exception:
                pass

        return stored

