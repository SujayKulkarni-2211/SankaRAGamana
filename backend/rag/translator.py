"""
Inbound translation only — converts non-English queries to English
before they enter the profiler/retriever/generator pipeline.

Outbound translation (English response → Kannada/Hindi) is handled
on the frontend. Sanskrit quotes in responses are marked with
data-notranslate so the frontend can skip them.
"""

from backend.rag.groq_client import get_client

_TRANSLATE_PROMPT = """Translate the following query into English.
Return only the translated text, nothing else. No explanation.

Query: {query}"""


async def translate_query_to_english(query: str, language: str) -> str:
    """
    If language is kn or hi, translate the query to English.
    sa and en pass through unchanged.
    """
    if language in ("en", "sa"):
        return query
    try:
        response = get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": _TRANSLATE_PROMPT.format(query=query)}],
            temperature=0.1,
            max_tokens=256,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[translator] inbound translation failed: {e}")
        return query  # fallback: use original query
