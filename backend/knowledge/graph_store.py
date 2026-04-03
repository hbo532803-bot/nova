from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from backend.database import get_db
from backend.db_retry import run_db_write_with_retry


class KnowledgeGraphStore:
    """
    Lightweight knowledge graph (SQLite):
    - nodes: (type, key) -> data blob
    - edges: (source)->(target) with relation + optional weight
    """

    def ensure(self) -> None:
        # Schema is owned by db_init; this is a defensive ensure for runtime usage.
        return None

    def upsert_node(self, node_type: str, node_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure()
        now = datetime.utcnow()
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_nodes (node_type, node_key, data, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(node_type, node_key)
                DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at
                """,
                (node_type, node_key, json.dumps(data), now),
            )
            conn.commit()
            return None

        run_db_write_with_retry("knowledge_nodes.upsert", _write)
        return {"ok": True, "node": {"type": node_type, "key": node_key}}

    def add_edge(
        self,
        source_type: str,
        source_key: str,
        relation: str,
        target_type: str,
        target_key: str,
        *,
        weight: float = 1.0,
    ) -> Dict[str, Any]:
        self.ensure()
        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_edges
                (source_type, source_key, relation, target_type, target_key, weight)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source_type, source_key, relation, target_type, target_key, float(weight)),
            )
            conn.commit()
            return None

        run_db_write_with_retry("knowledge_edges.insert", _write)
        return {"ok": True}

    def summary(self) -> Dict[str, Any]:
        self.ensure()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as n FROM knowledge_nodes")
            nodes = int(cursor.fetchone()["n"])
            cursor.execute("SELECT COUNT(*) as n FROM knowledge_edges")
            edges = int(cursor.fetchone()["n"])
        return {"nodes": nodes, "edges": edges}

    def neighbors(self, node_type: str, node_key: str, *, limit: int = 50) -> Dict[str, Any]:
        self.ensure()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT relation, target_type, target_key, weight, created_at
                FROM knowledge_edges
                WHERE source_type=? AND source_key=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (node_type, node_key, int(limit)),
            )
            out = [dict(r) for r in cursor.fetchall()]
        return {"node": {"type": node_type, "key": node_key}, "neighbors": out}

    def find_path(
        self,
        source_type: str,
        source_key: str,
        target_type: str,
        target_key: str,
        *,
        max_depth: int = 3,
        limit: int = 200,
    ) -> Dict[str, Any]:
        """
        Best-effort BFS path search over directed edges (bounded).
        """
        self.ensure()
        max_depth = max(1, min(int(max_depth), 6))

        start = (source_type, source_key)
        goal = (target_type, target_key)
        if start == goal:
            return {"ok": True, "path": [start]}

        # Load edges (bounded)
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT source_type, source_key, relation, target_type, target_key
                FROM knowledge_edges
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            rows = [dict(r) for r in cursor.fetchall()]

        adj: Dict[tuple[str, str], list[tuple[str, str, str]]] = {}
        for r in rows:
            s = (str(r["source_type"]), str(r["source_key"]))
            t = (str(r["target_type"]), str(r["target_key"]))
            rel = str(r["relation"])
            adj.setdefault(s, []).append((rel, t[0], t[1]))

        from collections import deque

        q = deque([(start, [start], 0)])
        seen = {start}
        while q:
            node, path, depth = q.popleft()
            if depth >= max_depth:
                continue
            for rel, nt, nk in adj.get(node, []):
                nxt = (nt, nk)
                if nxt in seen:
                    continue
                npath = path + [("REL", rel), nxt]
                if nxt == goal:
                    return {"ok": True, "path": npath}
                seen.add(nxt)
                q.append((nxt, npath, depth + 1))

        return {"ok": False, "path": []}

