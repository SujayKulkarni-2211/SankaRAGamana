"""
Seeker Profiler — runs BEFORE retrieval.

A Guru meets the seeker where they are. Before Shankara can respond,
the system must understand WHO is asking and WHY.
"""

import copy
import json
import os
from typing import Optional

from backend.rag.groq_client import get_client


PROFILER_PROMPT = """You are a profiler. Analyze the seeker's query and return a JSON object.

Seeker's query: "{query}"

Return ONLY valid JSON, no explanation, no markdown fences. Like this:
{{
  "level": "<beginner|intermediate|advanced|scholar>",
  "intent": "<definitional|philosophical|personal|devotional|in_distress>",
  "language": "<en|sa|kn|hi>",
  "emotional_tone": "<curious|distressed|devotional|analytical>",
  "retrieval_strategy": {{
    "primary_texts": [...],
    "top_k": <3-8>,
    "include_commentary": <true|false>
  }}
}}

LEVEL RULES:
- beginner: simple vocabulary, short question, "what is X", no Sanskrit
- intermediate: conceptual questions, some Sanskrit terms, familiarity with Vedanta
- advanced: uses Sanskrit freely, asks about bhashya, cites texts, technical depth
- scholar: deep textual questions, pūrvapakṣa-style, asks about commentary differences

INTENT RULES:
- definitional: "what is X", "define", "explain"
- philosophical: "how", "why", "what is the nature of"
- personal: "I am", "I feel", "how do I", "my life"
- devotional: Shiva, Devi, prayer, worship, grace, bhakti
- in_distress: grief, suffering, meaninglessness, loss, fear, "no point", "why live"

LANGUAGE RULES:
- en: English
- sa: Sanskrit (Devanagari or ITRANS)
- kn: Kannada
- hi: Hindi

PRIMARY TEXTS by profile:
- beginner/definitional → ["tattvabodha", "atmabodha", "bhajagovindam"]
- beginner/in_distress → ["bhajagovindam", "nirvanashatakam", "manishapanchakam"]
- intermediate → ["vivekachudamani", "aparokshanubhuti", "upadeshasahasri"]
- advanced/scholar → ["brahmasutra_bhashya", "gitabhashya", "kena_bhashya", "isha_bhashya", "upadeshasahasri", "vivekachudamani"]
- devotional (Shiva/general) → ["dakshinamurti_stotram", "kalabhairava_ashtakam", "bhajagovindam"]
- devotional (philosophical) → ["dakshinamurti_stotram", "vivekachudamani", "atmabodha"]
- in_distress → ["bhajagovindam", "nirvanashatakam", "manishapanchakam"]

TOP_K RULES:
- beginner: 4
- in_distress: 3
- intermediate: 5
- advanced: 7
- scholar: 8
- devotional: 4

INCLUDE_COMMENTARY:
- true for: beginner, in_distress, devotional
- false for: intermediate, advanced, scholar
"""

# Fallback profile when Groq call fails or returns bad JSON
DEFAULT_PROFILE = {
    "level": "intermediate",
    "intent": "philosophical",
    "language": "en",
    "emotional_tone": "curious",
    "retrieval_strategy": {
        "primary_texts": ["vivekachudamani", "tattvabodha", "atmabodha"],
        "top_k": 5,
        "include_commentary": False,
    },
}


def _detect_language_fallback(query: str) -> str:
    """Quick heuristic language detection without langdetect."""
    # Devanagari range
    if any("ऀ" <= c <= "ॿ" for c in query):
        # Distinguish Sanskrit from Hindi/Kannada roughly by script alone
        return "sa"
    # Kannada script
    if any("ಀ" <= c <= "೿" for c in query):
        return "kn"
    return "en"


MAX_HISTORY_CHARS = 3000  # chars of history injected into profiler context


def _compress_history(history: list) -> str:
    """
    Extractively compress history — keep the most recent turns that fit.
    No LLM call. Drops oldest turns first when over limit.
    Returns a formatted string summary or empty string.
    """
    if not history:
        return ""
    # Keep only the last 6 messages (3 exchanges), most recent first
    recent = history[-6:]
    # Build from most recent backward, stop when over char limit
    lines = []
    total = 0
    for msg in reversed(recent):
        role = "Seeker" if msg.get("role") == "user" else "Shankara"
        # Truncate each message to 400 chars to prevent one huge message dominating
        content = msg.get("content", "")[:400]
        line = f"{role}: {content}"
        if total + len(line) > MAX_HISTORY_CHARS:
            break
        lines.insert(0, line)
        total += len(line)
    if not lines:
        return ""
    return "Prior conversation (most recent first):\n" + "\n".join(lines)


async def profile_seeker(query: str, history: list = None) -> dict:
    """
    Analyze the seeker's query and return a profile dict.
    Falls back to DEFAULT_PROFILE if Groq is unavailable or returns bad JSON.
    """
    try:
        history_ctx = _compress_history(history or [])
        prompt = PROFILER_PROMPT.format(query=query)
        if history_ctx:
            prompt = history_ctx + "\n\nCurrent query: " + query + "\n\n" + prompt
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model ignores instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        profile = json.loads(raw)

        # Validate required keys exist; fill from deep-copied defaults if missing
        defaults = copy.deepcopy(DEFAULT_PROFILE)
        for key in ("level", "intent", "language", "emotional_tone", "retrieval_strategy"):
            if key not in profile:
                profile[key] = defaults[key]

        rs = profile.get("retrieval_strategy", {})
        if "primary_texts" not in rs:
            rs["primary_texts"] = defaults["retrieval_strategy"]["primary_texts"]
        if "top_k" not in rs:
            rs["top_k"] = defaults["retrieval_strategy"]["top_k"]
        if "include_commentary" not in rs:
            rs["include_commentary"] = defaults["retrieval_strategy"]["include_commentary"]

        # Override language with script-based detection if needed
        if profile.get("language") == "en":
            detected = _detect_language_fallback(query)
            if detected != "en":
                profile["language"] = detected

        profile["_history_ctx"] = _compress_history(history or [])
        _apply_hard_overrides(query, profile)
        return profile

    except Exception:
        # Never fail the request — just use the default profile
        profile = copy.deepcopy(DEFAULT_PROFILE)
        profile["language"] = _detect_language_fallback(query)
        profile["_history_ctx"] = _compress_history(history or [])
        _apply_hard_overrides(query, profile)
        return profile


_ATMAN_TERMS = {"atman", "ātman", "atma", "ātma", "soul", "self", "आत्मा", "आत्मन्", "आत्म"}


def _apply_hard_overrides(query: str, profile: dict) -> None:
    """
    Post-processing rules that override profiler output regardless of what
    the model returned. These encode domain knowledge the LLM may miss.
    """
    query_lower = query.lower()
    rs = profile.setdefault("retrieval_strategy", {})
    primary = rs.setdefault("primary_texts", [])

    # Atman definitional queries → tattvabodha and atmabodha must be first
    if profile.get("intent") == "definitional" and any(t in query_lower for t in _ATMAN_TERMS):
        for text in ("aatmabodha", "tattvabodha"):
            if text in primary:
                primary.remove(text)
            primary.insert(0, text)

    # Brahman/causation/creation queries → BSB is the primary source
    _BRAHMAN_TERMS = {"brahman", "brahma", "ब्रह्म", "brahmasutra", "vedanta", "cause of universe",
                      "creation", "srishti", "jagat karan", "anandamaya", "sarira"}
    if any(t in query_lower for t in _BRAHMAN_TERMS):
        if "brahmasutra_bhashya" not in primary:
            primary.insert(0, "brahmasutra_bhashya")

    # Karma yoga / Gita / dharma / arjuna queries → Gita Bhashya first
    _GITA_TERMS = {"karma yoga", "karmayoga", "bhagavad gita", "gita", "arjuna", "dharma",
                   "nishkama karma", "action", "duty", "karma", "कर्मयोग", "गीता", "अर्जुन"}
    if any(t in query_lower for t in _GITA_TERMS):
        if "gitabhashya" not in primary:
            primary.insert(0, "gitabhashya")

    # Deity-specific queries → the matching stotra must lead retrieval.
    # Each deity maps to the Shankara stotra(s) that praise/describe it.
    _DEITY_TEXTS = {
        ("ganesha", "ganapati", "vinayaka", "गणेश", "गणपति", "विनायक"):
            ["ganesha_pancharatnam"],
        ("shiva", "dakshinamurti", "dakshinamurthy", "शिव", "दक्षिणामूर्ति", "nataraja"):
            ["dakshina"],
        ("bhairava", "kalabhairava", "kala bhairava", "भैरव", "कालभैरव"):
            ["kaalabhairava"],
        ("devi", "shakti", "saraswati", "sharada", "देवी", "शारदा", "सरस्वती"):
            ["bhajagovindam"],
        ("guru", "गुरु", "teacher"):
            ["guruashtakam"],
    }
    for terms, texts in _DEITY_TEXTS.items():
        if any(t in query_lower for t in terms):
            for text in reversed(texts):
                if text in primary:
                    primary.remove(text)
                primary.insert(0, text)
            break
