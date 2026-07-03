"""
Persistent seeker memory — the "sleep consolidation".

A Guru remembers the seeker across visits. This module keeps one durable,
slowly-settled profile per logged-in user, distilled OFFLINE from their
accumulated conversations, and blends it into the live per-query profile so
retrieval and tone reflect who the seeker has shown themselves to be.

Flow:
  - load_profile(user_id)            → the stored durable profile (or None)
  - blend_into(profile, stored)      → fold durable signals into the live profile
  - is_stale(stored, n_recent)       → has enough changed to re-consolidate?
  - consolidate(user_id)             → the sleep pass: LLM distills history → store
                                       (run in the background, never blocks a query)

The per-query profiler (seeker_profiler.py) stays the live, ephemeral read of
the current question. This is the long memory it leans on. See [[philosophy-guru-model]].
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from supabase import create_client, Client

from backend.rag.groq_client import chat as groq_chat, MODEL_LIGHT

# Re-consolidate when the seeker has had this many exchanges since the last pass,
# OR when the profile is older than this. Whichever comes first.
STALE_EXCHANGES = 5
STALE_AGE = timedelta(hours=24)

# How many recent exchanges the sleep pass reads to distill the profile.
CONSOLIDATE_WINDOW = 30

_db: Optional[Client] = None


def _db_client() -> Client:
    global _db
    if _db is None:
        _db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _db


# ── Load / store ──────────────────────────────────────────────────────────────

def load_profile(user_id: str) -> Optional[dict]:
    """Return the stored durable profile for a user, or None. Never raises."""
    if not user_id:
        return None
    try:
        res = _db_client().table("seeker_profiles").select("*").eq(
            "user_id", user_id
        ).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"[seeker_memory] load failed: {e}")
        return None


def _count_exchanges(user_id: str) -> int:
    try:
        res = _db_client().table("conversations").select(
            "session_id", count="exact"
        ).eq("user_id", user_id).execute()
        return res.count or 0
    except Exception:
        return 0


# ── Staleness ─────────────────────────────────────────────────────────────────

def is_stale(stored: Optional[dict], total_exchanges: int) -> bool:
    """Should we re-run the sleep pass for this seeker?"""
    if stored is None:
        # No durable profile yet — consolidate once there's something to learn from.
        return total_exchanges >= 1
    seen = stored.get("n_exchanges_seen", 0) or 0
    if total_exchanges - seen >= STALE_EXCHANGES:
        return True
    last = stored.get("last_consolidated_at")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) - last_dt > STALE_AGE:
            return True
    except Exception:
        return True
    return False


# ── Blend durable profile into the live per-query profile ─────────────────────

# A seeker who has come back more than this many times is no longer a stranger
# being met for the first time — treat them as advanced.
ADVANCED_AFTER_EXCHANGES = 2


def blend_into(profile: dict, stored: Optional[dict], total_exchanges: int = 0) -> dict:
    """
    Fold durable signals into the live per-query profile. The live read of the
    CURRENT question always wins on intent/language (the seeker may ask anything
    today), but the durable profile informs level, tone, and surfaces texts that
    have served this seeker — and hands the synthesis a short note on who they are.
    Mutates and returns `profile`.

    `total_exchanges` is the count of past exchanges for this seeker; once it
    exceeds ADVANCED_AFTER_EXCHANGES the seeker is treated as advanced.
    """
    # A returning seeker who has engaged more than twice is treated as advanced,
    # regardless of the durable or live level. Applies even before the first
    # consolidation (stored may be None), as long as we know the count.
    if total_exchanges > ADVANCED_AFTER_EXCHANGES:
        profile["level"] = "advanced"

    if not stored:
        return profile

    # Level: trust the durable read when the live read is the bland default.
    # The seeker's demonstrated depth across visits is a better prior than one
    # line — but never below what the exchange-count rule already established.
    if (stored.get("level")
            and profile.get("level") in (None, "intermediate")
            and total_exchanges <= ADVANCED_AFTER_EXCHANGES):
        profile["level"] = stored["level"]

    # Tone: a seeker who has shown distress/devotion carries it between visits;
    # let the durable tone stand unless the live read detected distress now.
    if stored.get("tone") and profile.get("emotional_tone") not in ("distressed",):
        profile.setdefault("_durable_tone", stored["tone"])

    # Affinity texts → nudged into retrieval as a soft boost (NOT a hard filter).
    rs = profile.setdefault("retrieval_strategy", {})
    primary = rs.setdefault("primary_texts", [])
    for t in (stored.get("affinity_texts") or []):
        if t not in primary:
            primary.append(t)

    # A short note the synthesis/reflection can use to meet the seeker as someone
    # known, not a stranger. Carried on the profile; consumers may ignore it.
    if stored.get("notes"):
        profile["_seeker_notes"] = stored["notes"]
    if stored.get("recurring_themes"):
        profile["_recurring_themes"] = stored["recurring_themes"]

    return profile


# ── The sleep pass: distill durable profile from history ──────────────────────

CONSOLIDATE_PROMPT = """You are distilling a durable profile of a spiritual seeker \
from their recent conversations with a Vedanta teacher. This is long-term memory: \
who this seeker IS across visits, not what they asked once.

Recent exchanges (most recent first):
{history}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "level": "<beginner|intermediate|advanced|scholar>",
  "dominant_intent": "<definitional|philosophical|personal|devotional|in_distress>",
  "language": "<en|sa|kn|hi>",
  "tone": "<curious|distressed|devotional|analytical>",
  "recurring_themes": ["...up to 5 short theme words, e.g. atman, maya, suffering..."],
  "affinity_texts": ["...up to 4 text names that recur or clearly served this seeker..."],
  "notes": "<ONE short paragraph (2-3 sentences) describing this seeker as a teacher would remember them — their depth, what they keep returning to, how to meet them. No invented facts.>"
}}

Judge from the WHOLE pattern, not the last message. If the seeker grows more \
advanced over time, reflect the trajectory. Be specific and grounded in what is \
actually there."""


def _format_history(rows: list) -> str:
    lines = []
    for r in rows:
        q = (r.get("query") or "").strip()[:300]
        prof = r.get("seeker_profile") or {}
        tag = ""
        if isinstance(prof, dict):
            tag = f" [{prof.get('level','?')}/{prof.get('intent','?')}]"
        if q:
            lines.append(f"- {q}{tag}")
    return "\n".join(lines) if lines else "(no exchanges)"


def consolidate(user_id: str) -> Optional[dict]:
    """
    The sleep pass. Reads the seeker's recent conversations, distills a durable
    profile with one LLM call, and upserts it. Returns the stored row or None.
    Safe to run in the background — never raises, never blocks a query.
    """
    if not user_id:
        return None
    try:
        db = _db_client()
        res = db.table("conversations").select(
            "query, seeker_profile, created_at"
        ).eq("user_id", user_id).order(
            "created_at", desc=True
        ).limit(CONSOLIDATE_WINDOW).execute()
        rows = res.data or []
        total = _count_exchanges(user_id)
        if not rows:
            return None

        prompt = CONSOLIDATE_PROMPT.format(history=_format_history(rows))
        response = groq_chat(
            model=MODEL_LIGHT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        distilled = json.loads(raw)

        # Cap everything at the source so the stored profile — and every prompt
        # it later feeds — stays small no matter what the model returns.
        notes = (distilled.get("notes") or "").strip()[:280]
        themes = [str(t).strip()[:24] for t in (distilled.get("recurring_themes") or [])][:5]
        affinity = [str(t).strip()[:40] for t in (distilled.get("affinity_texts") or [])][:4]
        row = {
            "user_id": user_id,
            "level": distilled.get("level"),
            "dominant_intent": distilled.get("dominant_intent"),
            "language": distilled.get("language"),
            "tone": distilled.get("tone"),
            "recurring_themes": themes,
            "affinity_texts": affinity,
            "notes": notes,
            "n_exchanges_seen": total,
            "last_consolidated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        db.table("seeker_profiles").upsert(row, on_conflict="user_id").execute()
        print(f"[seeker_memory] consolidated {user_id}: "
              f"{row['level']}/{row['dominant_intent']}, "
              f"{len(row['recurring_themes'])} themes, {total} exchanges")
        return row
    except Exception as e:
        print(f"[seeker_memory] consolidate failed for {user_id}: {e}")
        return None
