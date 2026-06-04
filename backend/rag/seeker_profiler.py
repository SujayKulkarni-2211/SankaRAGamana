"""
Seeker Profiler — runs BEFORE retrieval.

A Guru meets the seeker where they are. Before Shankara can respond,
the system must understand WHO is asking and WHY.
"""

import copy
import json
import os
from typing import Optional

from groq import Groq

_client: Optional[Groq] = None

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
- advanced/scholar → ["kena_bhashya", "isha_bhashya", "upadeshasahasri", "vivekachudamani"]
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


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


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


async def profile_seeker(query: str) -> dict:
    """
    Analyze the seeker's query and return a profile dict.
    Falls back to DEFAULT_PROFILE if Groq is unavailable or returns bad JSON.
    """
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": PROFILER_PROMPT.format(query=query)},
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

        return profile

    except Exception:
        # Never fail the request — just use the default profile
        profile = copy.deepcopy(DEFAULT_PROFILE)
        profile["language"] = _detect_language_fallback(query)
        return profile
