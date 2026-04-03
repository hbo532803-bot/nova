import json
import math
import os
from backend.database import get_db
from backend.db_retry import run_db_write_with_retry
from google import genai

# Gemini client
client = None
if os.getenv("GEMINI_API_KEY"):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_embedding(text: str):
    if not client:
        return None

    try:
        response = client.models.embed_content(
            model="models/embedding-001",
            content=text
        )
        return response.embedding
    except Exception:
        return None


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)


class ReflectionMemory:

    # ----------------------------
    # STORE REFLECTION
    # ----------------------------
    def record_reflection(self, data: dict):

        embedding = get_embedding(data.get("input_objective", ""))

        def _write(conn):
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reflections (
                    cycle_id,
                    primary_goal,
                    input_objective,
                    execution_result,
                    success,
                    confidence_before,
                    confidence_after,
                    embedding
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(data.get("cycle_id")),
                    str(data.get("primary_goal_snapshot")),
                    str(data.get("input_objective")),
                    str(data.get("execution_result")),
                    1 if data.get("success") else 0,
                    float(data.get("confidence_before") or 0),
                    float(data.get("confidence_after") or 0),
                    json.dumps(embedding) if embedding else None,
                ),
            )
            conn.commit()
            return None

        run_db_write_with_retry("reflections.insert", _write)

    # ----------------------------
    # EXACT MATCH HISTORY
    # ----------------------------
    def recent_similar(self, goal: str, limit: int = 5):

        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT input_objective, success
                FROM reflections
                WHERE input_objective = ?
                ORDER BY id DESC
                LIMIT ?
            """, (goal, limit))

            return cursor.fetchall()

    # ----------------------------
    # SEMANTIC SEARCH
    # ----------------------------
    def semantic_search(self, query: str, threshold: float = 0.85):

        query_embedding = get_embedding(query)
        if not query_embedding:
            return None

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT input_objective, embedding
                FROM reflections
                WHERE embedding IS NOT NULL
            """)
            rows = cursor.fetchall()

        for goal, emb in rows:
            stored = json.loads(emb)
            similarity = cosine(query_embedding, stored)
            if similarity >= threshold:
                return goal

        return None
