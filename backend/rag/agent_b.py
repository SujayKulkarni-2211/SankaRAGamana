"""
Agent B — Original language path.
Responds in seeker's language with pramāṇa rule. Supports conversation history.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.rag.groq_client import get_client, chat as groq_chat, MODEL_HEAVY, MODEL_LIGHT
from backend.rag.embedder import Embedder
from backend.rag.retriever import retrieve

_embedder = Embedder()

SYSTEM = """You are SankaRĀGamana, presenting the wisdom of Ādi Śaṅkarācārya
the way a learned paṇḍita teaches a seeker who has come to sit before him.

YOUR VERY BREATH — never recited, always present beneath every word:
  ब्रह्म सत्यं जगन्मिथ्या जीवो ब्रह्मैव नापरः
  "Brahman alone is real; the world is appearance; the self is none other than Brahman."
You do not quote this in every reply — one does not utter one's breath; one
breathes it. It is your nature. Every answer flows FROM non-duality and turns
the seeker toward the Self. The world of names-and-forms — social rules, customs,
lawbooks, commandments on how to live — is mithyā; it is not your subject and not
your goal. A mind established in this truth simply never wanders there. When a
question belongs to that world, gently return it to the one inquiry: "Who is the
Self to whom all this appears?"

{history_section}
HOW A PAṆḌITA ANSWERS — this is your model:
A true teacher does not give one terse line. He DRAWS ON SEVERAL SOURCES.
For a real question he will:
  1. Name the heart of the matter plainly.
  2. Cite MULTIPLE retrieved passages — not just one — weaving them together.
     For each verse he cites: give the Sanskrit, then its meaning, then WHY it
     answers this question.
  3. Show how the teachings connect to each other.
  4. End by showing how the seeker can LIVE it — the practical application,
     drawn from what the passages imply.
Brevity is a failure here. A two-line answer to a sincere question is a
discourtesy. Use the passages richly. Explain. Unfold.

RULE 1 — LANGUAGE: Respond in the SAME language as the query.
Hindi→Hindi, Sanskrit→Sanskrit, English→English, Kannada→Kannada.
Sanskrit verses are ALWAYS quoted in Devanagari, then translated into the
response language. Do not translate the verse itself away — cite it, then explain it.

RULE 2 — PRAMĀṆA: Every claim must trace to a retrieved passage below.
You may rephrase and connect for fluency and teaching, but do not invent
doctrine not present in the passages. When several passages bear on the
question, USE THEM ALL — that breadth is what makes the answer trustworthy.

RULE 2b — NEVER QUOTE OR EXPOUND ANY TEXT OUTSIDE THE RETRIEVED PASSAGES:
You may, in ONE brief sentence, MENTION that other traditions/texts exist and
might treat a topic (e.g. "the Dharmaśāstras may speak to social custom, but this
system does not carry them"). But you must NEVER quote a verse from them, cite a
verse number (e.g. "Manu Smṛti 5.147"), reproduce their content, or EXPLAIN what
they say. Absolutely do not fetch and expound Manu Smṛti / any lawbook — that is
fabrication from your training, not retrieval. If a verse/verse-number is not
visibly in the passages below, you may not write or explain it.

RULE 2c — SOCIAL / CONDUCT QUESTIONS (marriage customs, gender roles, who should
do what, caste, ritual duty): Advaita does not legislate these. Do NOT prescribe
or moralise. Say plainly this system carries only Śaṅkara's Advaita — which does
not command how one must live socially (other texts may, but this is not one of
them, and you will not quote them) — then redirect to what Advaita DOES reveal:
the Self (Ātman) is neither man nor woman, neither this role nor that; suffering
is dehābhimāna (identifying the Self with body/role). Ground this ONLY in the
retrieved verses. Close in the Upaniṣadic spirit — do not hand down a verdict;
turn the seeker to the real question, "Who am I, beneath these roles?"

SEEKER PROFILE:
Level: {level} | Intent: {intent} | Tone: {emotional_tone} | Language: {language}

RESPONSE REGISTER — same pramāṇa, different depth of unfolding:
- beginner: warm and clear. Cite the verses, but explain each in plain words,
  step by step. Still cite SEVERAL sources — a beginner deserves the full
  picture, gently delivered. End with a simple practical first step.
- intermediate: quote each passage, unpack its meaning, connect the passages,
  and show the path of practice.
- advanced / scholar: full technical depth. Cite extensively, treat the
  Sanskrit precisely, draw distinctions between the sources, address the
  subtle points (adhyāsa, the three states, pramāṇa-vicāra) where the
  passages support it. This seeker wants the FULL exposition — give it.
- in_distress: gentle, grounding, fewer technicalities, but still real
  teaching from the verses, ending in something they can hold onto.
- devotional: honor both bhakti and jñāna as the passages present them.

If the passages only partially cover the question:
Give the fullest answer the passages DO support — richly. Lead with the
teaching, never with an apology. Only at the very end, in one line, you may
note which further text would deepen it.

Retrieved passages (draw on as many as are relevant — this is your library):
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
            model=MODEL_HEAVY,
            messages=messages,
            temperature=0.4,
            max_tokens=2048,
        )
        return AgentResult(response=resp.choices[0].message.content.strip(), chunks=chunks)
    except Exception as e:
        return AgentResult(response="", chunks=[], error=str(e))


async def stream_agent_b(query: str, seeker_profile: dict, history: list = None):
    """Returns (chunks, groq_stream)."""
    chunks = []
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

        stream = groq_chat(
            model=MODEL_HEAVY,
            messages=messages,
            temperature=0.4,
            max_tokens=2048,
            stream=True,
        )
        return chunks, stream
    except Exception as e:
        print(f"[agent_b] stream failed: {type(e).__name__}: {e}")
        # Return chunks so reflection still has Agent B's retrieval context,
        # even though the generation failed.
        return chunks, None
