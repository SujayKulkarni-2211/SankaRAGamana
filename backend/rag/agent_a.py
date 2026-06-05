"""
Agent A — Sanskrit path.
Translates query to Sanskrit, retrieves, generates in Sanskrit.
Supports both regular and streaming generation.
"""

from dataclasses import dataclass
from typing import List, Optional

from backend.rag.groq_client import get_client
from backend.rag.embedder import Embedder
from backend.rag.retriever import retrieve

_embedder = Embedder()

TRANSLATE_PROMPT = """Translate the following to Sanskrit only.
Return only Devanagari Sanskrit. No explanation, no transliteration, no English. Only Sanskrit.
Text: {query}"""

SYSTEM = """You are SankaRĀGamana presenting the wisdom of Ādi Śaṅkarācārya.
Retrieved passages from Shankara's texts are provided. Present them to answer the seeker's question.
Respond entirely in Sanskrit (Devanagari script).

PRAMĀṆA RULE:
- Every claim must trace to a retrieved passage
- Quote Sanskrit verbatim from retrieved passages only
- If passages do not answer fully: इदं विषयं पूर्णतया नास्ति — and name the text needed
- Do NOT extend a teaching to subjects not named in the retrieved chunk
- Do NOT invent Sanskrit not in the retrieved text

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
    r = get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
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
        resp = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
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
        stream = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
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
        return "", [], None
