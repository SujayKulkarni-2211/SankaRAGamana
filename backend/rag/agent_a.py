"""
Agent A — Sanskrit path.
Translates query to Sanskrit, retrieves, generates in Sanskrit.
Supports both regular and streaming generation.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.rag.groq_client import get_client, chat as groq_chat, MODEL_HEAVY, MODEL_LIGHT
from backend.rag.embedder import Embedder
from backend.rag.retriever import retrieve

_embedder = Embedder()

TRANSLATE_PROMPT = """Translate the seeker's question into pure classical Sanskrit
(संस्कृतम्) — the language of Śaṅkara's texts. NOT Hindi, NOT Sanskritised Hindi.

Rules:
- Use classical Sanskrit vocabulary and grammar (vibhakti, correct case endings).
- Keep proper names in their Sanskrit form (Ganesha→गणेशः, Self→आत्मन्).
- Output ONLY the Devanagari Sanskrit question. No transliteration, no English,
  no explanation, no quotes.
- It must read as a question a paṇḍita would actually ask.

Text: {query}"""

SYSTEM = """You are SankaRĀGamana presenting the wisdom of Ādi Śaṅkarācārya.
Retrieved passages from Shankara's texts are provided. Present them to answer the seeker's question.
Respond entirely in Sanskrit (Devanagari script).

तव प्राणः — YOUR BREATH (never recited, always present):
ब्रह्म सत्यं जगन्मिथ्या जीवो ब्रह्मैव नापरः ।
This is your nature, not a line to repeat. Every answer flows from advaita and
turns the seeker toward the आत्मन्. The world of social rules and conduct
(व्यवहार, धर्मशास्त्र) is मिथ्या — not your subject. A mind fixed in this truth
never wanders there; it returns every question to the one inquiry: आत्मा कः?

PRAMĀṆA RULE:
- Every claim must trace to a retrieved passage
- Quote Sanskrit verbatim from retrieved passages only
- If passages do not answer fully: इदं विषयं पूर्णतया अत्र नास्ति — say so honestly
- Do NOT extend a teaching to subjects not named in the retrieved chunk
- Do NOT invent Sanskrit not in the retrieved text

निषेधः — FORBIDDEN:
- Do NOT quote a verse from, cite a verse-number of, or EXPLAIN the content of
  ANY text outside the retrieved passages — especially NOT मनुस्मृति (Manu
  Smṛti), धर्मशास्त्र (dharmaśāstra), or any lawbook of social conduct. You may
  in ONE line merely note such texts exist elsewhere, but NEVER reproduce or
  expound them. This is केवलाद्वैतवेदान्तम् — pure Advaita Vedānta; it gives no
  social commandments.
- If the question is about social roles, conduct, marriage, gender, caste, or
  duty (not the nature of the Self), do NOT prescribe. Instead point to what
  Advaita reveals: आत्मा न स्त्री न पुरुषः — the Self is neither woman nor man,
  beyond the body and its roles. Use ONLY the retrieved verses to say this.

Retrieved passages:
{chunks_formatted}"""


@dataclass
class AgentResult:
    response: str
    chunks: List[dict]
    sanskrit_query: str = ""
    error: Optional[str] = None


def _fmt(chunks: List[dict]) -> str:
    if not chunks:
        return "No passages retrieved."
    return "\n\n".join(
        f"[{i+1}] {c.get('text_name','?')}, v.{c.get('verse_number','?')}\n{c.get('content','')}"
        for i, c in enumerate(chunks)
    )


async def translate_to_sanskrit(query: str) -> str:
    r = groq_chat(
        model=MODEL_HEAVY,
        messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(query=query)}],
        temperature=0.1,
        max_tokens=200,
    )
    return r.choices[0].message.content.strip()


async def run_agent_a(query: str, seeker_profile: dict) -> AgentResult:
    try:
        sanskrit_query = await translate_to_sanskrit(query)
        sa_embedding = _embedder.embed_query(sanskrit_query)
        chunks = await retrieve(sa_embedding, seeker_profile)
        resp = groq_chat(
            model=MODEL_HEAVY,
            messages=[
                {"role": "system", "content": SYSTEM.format(chunks_formatted=_fmt(chunks))},
                {"role": "user", "content": f"The seeker asks: {sanskrit_query}"},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return AgentResult(
            response=resp.choices[0].message.content.strip(),
            chunks=chunks,
            sanskrit_query=sanskrit_query,
        )
    except Exception as e:
        return AgentResult(response="", chunks=[], sanskrit_query="", error=str(e))


async def stream_agent_a(query: str, seeker_profile: dict):
    """Returns (sanskrit_query, chunks, groq_stream)."""
    try:
        sanskrit_query = await translate_to_sanskrit(query)
        sa_embedding = _embedder.embed_query(sanskrit_query)
        chunks = await retrieve(sa_embedding, seeker_profile)
        stream = groq_chat(
            model=MODEL_HEAVY,
            messages=[
                {"role": "system", "content": SYSTEM.format(chunks_formatted=_fmt(chunks))},
                {"role": "user", "content": f"The seeker asks: {sanskrit_query}"},
            ],
            temperature=0.3,
            max_tokens=1024,
            stream=True,
        )
        return sanskrit_query, chunks, stream
    except Exception as e:
        print(f"[agent_a] stream failed: {type(e).__name__}: {e}")
        return "", [], None
