"""
Imprint distillation logic.

Negative feedback → immediate distillation (1 principle per failure).
Positive feedback → periodic distillation when threshold reached (every 20).
Imprints are loaded by the reflection agent at query time.
Always bounded: max 10 positive + 10 negative = 20 injected per query.
"""

import os
import json
from typing import List, Optional

from groq import Groq
from backend.rag.groq_client import MODEL_HEAVY
from supabase import create_client, Client

POSITIVE_DISTILLATION_THRESHOLD = 20

_groq: Optional[Groq] = None
_db: Optional[Client] = None

NEGATIVE_DISTILL_PROMPT = """This response received negative feedback from a seeker.

Query: {query}
Response: {response}
User feedback: {feedback_text}
Retrieved chunks used: {chunks}

In one sentence state the principle this failure teaches.
Be specific to what went wrong, not generic.
Return only the principle, nothing else."""

POSITIVE_DISTILL_PROMPT = """These {count} responses received positive feedback from seekers.

{responses}

Identify 3 principles that made these responses effective.
Each principle in one sentence. Be specific, not generic.
Return as a JSON array of 3 strings, nothing else. Example:
["principle one", "principle two", "principle three"]"""


def _groq_client() -> Groq:
    global _groq
    if _groq is None:
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq


def _db_client() -> Client:
    global _db
    if _db is None:
        _db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _db


def _upsert_imprint(principle: str, polarity: str):
    db = _db_client()
    # Check if similar principle already exists (substring match)
    existing = db.table("imprints").select("id, source_count").ilike(
        "principle", f"%{principle[:40]}%"
    ).eq("polarity", polarity).limit(1).execute()

    if existing.data:
        row = existing.data[0]
        new_count = row["source_count"] + 1
        new_conf = new_count / (new_count + 2)
        db.table("imprints").update({
            "source_count": new_count,
            "confidence": round(new_conf, 4),
            "updated_at": "NOW()",
        }).eq("id", row["id"]).execute()
    else:
        db.table("imprints").insert({
            "principle": principle,
            "polarity": polarity,
            "confidence": 0.5,
            "source_count": 1,
        }).execute()


async def distill_negative(
    query: str,
    response: str,
    feedback_text: str,
    chunks: list,
):
    """Called synchronously on negative feedback before returning to user."""
    try:
        chunks_preview = " | ".join(
            c.get("chunk_id", "") for c in (chunks or [])[:5]
        )
        raw = _groq_client().chat.completions.create(
            model=MODEL_HEAVY,
            messages=[{"role": "user", "content": NEGATIVE_DISTILL_PROMPT.format(
                query=query,
                response=response,
                feedback_text=feedback_text or "(no text provided)",
                chunks=chunks_preview,
            )}],
            temperature=0.1,
            max_tokens=100,
        )
        principle = raw.choices[0].message.content.strip()
        _upsert_imprint(principle, "negative")
    except Exception as e:
        print(f"[imprints] negative distillation failed: {e}")


async def maybe_distill_positive():
    """Check if we've hit the threshold and distill positive feedback."""
    db = _db_client()
    try:
        # Count unprocessed positive feedback
        count_result = db.table("feedback").select(
            "*", count="exact", head=True
        ).eq("rating", True).eq("processed_for_imprints", False).execute()
        count = count_result.count or 0

        if count < POSITIVE_DISTILLATION_THRESHOLD:
            return

        # Fetch the unprocessed positive feedbacks
        rows = db.table("feedback").select(
            "id, query, final_response, reflection_reasoning"
        ).eq("rating", True).eq("processed_for_imprints", False).limit(
            POSITIVE_DISTILLATION_THRESHOLD
        ).execute().data

        if not rows:
            return

        responses_text = "\n\n---\n\n".join(
            f"Query: {r['query']}\nResponse: {r['final_response']}"
            for r in rows
        )
        raw = _groq_client().chat.completions.create(
            model=MODEL_HEAVY,
            messages=[{"role": "user", "content": POSITIVE_DISTILL_PROMPT.format(
                count=len(rows),
                responses=responses_text[:6000],
            )}],
            temperature=0.2,
            max_tokens=300,
        )
        text = raw.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        principles = json.loads(text.strip())

        for principle in principles:
            _upsert_imprint(str(principle), "positive")

        # Mark feedbacks as processed
        ids = [r["id"] for r in rows]
        for fid in ids:
            db.table("feedback").update(
                {"processed_for_imprints": True}
            ).eq("id", fid).execute()

    except Exception as e:
        print(f"[imprints] positive distillation failed: {e}")


def load_imprints() -> dict:
    """Load top 10 positive + top 10 negative imprints for reflection agent."""
    db = _db_client()
    try:
        positive = db.table("imprints").select("principle, confidence").eq(
            "polarity", "positive"
        ).order("confidence", desc=True).limit(10).execute().data

        negative = db.table("imprints").select("principle, confidence").eq(
            "polarity", "negative"
        ).order("confidence", desc=True).limit(10).execute().data

        return {"positive": positive, "negative": negative}
    except Exception as e:
        print(f"[imprints] load failed: {e}")
        return {"positive": [], "negative": []}
