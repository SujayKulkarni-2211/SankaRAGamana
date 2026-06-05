"""
Agent B — Original language path.
Responds in seeker's language with pramāṇa rule. Supports conversation history.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.rag.groq_client import get_client
from backend.rag.embedder import Embedder
from backend.rag.retriever import retrieve

_embedder = Embedder()

SYSTEM = """You are SankaRĀGamana presenting the wisdom of Ādi Śaṅkarācārya.

{history_section}
RULE 1 — LANGUAGE: You must respond in the same language as the original query.
If query is Hindi → respond in Hindi.
If query is Sanskrit → respond in Sanskrit.
If query is English → respond in English.
If query is Kannada → respond in Kannada.
Mixing languages is forbidden.

RULE 2 — PRAMĀṆA: Every single sentence you write must trace directly to one of
the retrieved chunks provided below. You may rephrase for fluency.
You may NOT write any sentence that is not grounded in a retrieved chunk.
If you find yourself writing something not in the chunks — stop and do not write it.
A textbook description that is not from the retrieved chunks is a violation.
Silence is better than invention.

SEEKER PROFILE:
Level: {level} | Intent: {intent} | Tone: {emotional_tone} | Language: {language}

RESPONSE REGISTER:
- beginner or in_distress: speak simply, warmly; ground every statement in retrieved text
- intermediate: quote passage then unpack meaning for this question
- advanced/scholar: full Sanskrit with citations, technical precision
- devotional: honor both Bhakti and Jñāna from what was retrieved

If the retrieved passages address the question only partially:
Give the fullest answer possible from what IS retrieved. Present the pramāṇa available.
Only at the very end, in one sentence, note what additional texts would deepen the understanding.
Never open your response with an admission of incompleteness — lead with what Shankara said.

Retrieved passages:
{chunks_formatted}"""


@dataclass
class AgentResult:
    response: str
    chunks: List[dict]
    error: Optional[str] = None


def _fmt(chunks: List[dict]) -> str:
    if not chunks:
        return "No passages retrieved."
    return "\n\n".join(
        f"[{i+1}] {c.get('text_name','?')}, v.{c.get('verse_number','?')}"
        + (" [confirmed]" if c.get("authenticity") == "confirmed" else "")
        + f"\n{c.get('content','')}"
        for i, c in enumerate(chunks)
    )


def _history_messages(history: list) -> list:
    """Convert history list to Groq messages format, capped to last 6 messages."""
    if not history:
        return []
    recent = history[-6:]
    return [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in recent]


def _history_section(history: list) -> str:
    if not history:
        return ""
    ctx = seeker_profile_history_ctx if False else ""  # handled via profile
    return ""  # history is passed as messages, not injected into system prompt


async def run_agent_b(query: str, seeker_profile: dict, history: list = None) -> AgentResult:
    try:
        emb = _embedder.embed_query(query)
        chunks = await retrieve(emb, seeker_profile)

        history_ctx = seeker_profile.get("_history_ctx", "")
        history_section = f"CONVERSATION CONTEXT:\n{history_ctx}\n\n" if history_ctx else ""

        messages = [
            {"role": "system", "content": SYSTEM.format(
                history_section=history_section,
                level=seeker_profile.get("level", "intermediate"),
                intent=seeker_profile.get("intent", "philosophical"),
                emotional_tone=seeker_profile.get("emotional_tone", "curious"),
                language=seeker_profile.get("language", "en"),
                chunks_formatted=_fmt(chunks),
            )},
        ]
        # Inject prior turns as actual chat messages for the model to track
        messages.extend(_history_messages(history or []))
        messages.append({"role": "user", "content": f"The seeker asks: {query}"})

        resp = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
        )
        return AgentResult(response=resp.choices[0].message.content.strip(), chunks=chunks)
    except Exception as e:
        return AgentResult(response="", chunks=[], error=str(e))


async def stream_agent_b(query: str, seeker_profile: dict, history: list = None):
    """Returns (chunks, groq_stream)."""
    try:
        emb = _embedder.embed_query(query)
        chunks = await retrieve(emb, seeker_profile)

        history_ctx = seeker_profile.get("_history_ctx", "")
        history_section = f"CONVERSATION CONTEXT:\n{history_ctx}\n\n" if history_ctx else ""

        messages = [
            {"role": "system", "content": SYSTEM.format(
                history_section=history_section,
                level=seeker_profile.get("level", "intermediate"),
                intent=seeker_profile.get("intent", "philosophical"),
                emotional_tone=seeker_profile.get("emotional_tone", "curious"),
                language=seeker_profile.get("language", "en"),
                chunks_formatted=_fmt(chunks),
            )},
        ]
        messages.extend(_history_messages(history or []))
        messages.append({"role": "user", "content": f"The seeker asks: {query}"})

        stream = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
            stream=True,
        )
        return chunks, stream
    except Exception as e:
        return [], None
