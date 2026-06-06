"""
SSE streaming endpoint — POST /api/query/stream

Events in order:
1. profile
2. agent_a_translation
3. agent_a_chunks
4. agent_a_response  (token by token)
5. agent_b_chunks
6. agent_b_response  (token by token)
7. reflection_reasoning (token by token)
8. final_response (token by token)
9. done
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.rag.seeker_profiler import profile_seeker
from backend.rag.translator import translate_query_to_english
from backend.rag.agent_a import stream_agent_a, run_agent_a, AgentResult as AResult
from backend.rag.agent_b import stream_agent_b, run_agent_b, AgentResult as BResult
from backend.rag.reflection import run_reflection_agent
from backend.rag.imprints import load_imprints
from backend.api.rate_limit import check_rate_limits

router = APIRouter()


class HistoryMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class StreamRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    history: Optional[list[HistoryMessage]] = None  # prior turns for context


def sse(event: str, data) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def sse_json(event: str, text: str) -> str:
    """SSE event whose data is a JSON-encoded string.
    Preserves spaces and newlines through SSE framing — the frontend JSON.parses it."""
    return f"event: {event}\ndata: {json.dumps(text, ensure_ascii=False)}\n\n"


def chunk_preview(chunks: list) -> list:
    return [
        {
            "chunk_id": c.get("chunk_id", ""),
            "text_name": c.get("text_name", ""),
            "preview": c.get("content", "")[:60],
        }
        for c in chunks
    ]


async def generate_stream(question: str, user_id: Optional[str], client_ip: str, history: list = None) -> AsyncIterator[str]:
    # Rate limit check — before any LLM calls
    allowed, limit_msg, reset_at = await check_rate_limits(user_id, client_ip)
    if not allowed:
        yield sse("rate_limited", {
            "message": limit_msg,
            "reset_at": reset_at,
        })
        return

    # Step 1: Profile — pass history so level/intent reflects ongoing conversation
    seeker_profile = await profile_seeker(question, history=history)
    yield sse("profile", {
        "level": seeker_profile.get("level"),
        "intent": seeker_profile.get("intent"),
        "language": seeker_profile.get("language"),
        "emotional_tone": seeker_profile.get("emotional_tone"),
    })

    language = seeker_profile.get("language", "en")
    pipeline_q = await translate_query_to_english(question, language)

    # Step 2: Run Agent A and B setup in parallel (translation + retrieval)
    a_sa_query, a_chunks, a_stream = await stream_agent_a(pipeline_q, seeker_profile)
    b_chunks, b_stream = await stream_agent_b(pipeline_q, seeker_profile, history=history or [])

    # Step 3: Agent A translation + chunks
    yield sse_json("agent_a_translation", a_sa_query)
    yield sse("agent_a_chunks", chunk_preview(a_chunks))

    # Step 4: Stream Agent A tokens — JSON-encoded so spaces survive SSE framing
    a_full = ""
    if a_stream:
        for chunk in a_stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                a_full += token
                yield sse_json("agent_a_response", token)

    # Step 5: Agent B chunks
    yield sse("agent_b_chunks", chunk_preview(b_chunks))

    # Step 6: Stream Agent B tokens — JSON-encoded so spaces survive SSE framing
    b_full = ""
    if b_stream:
        for chunk in b_stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                b_full += token
                yield sse_json("agent_b_response", token)

    # Step 7: Run reflection (non-streaming — it produces JSON)
    # Build AgentResult objects from accumulated text
    a_result = AResult(response=a_full, chunks=a_chunks, sanskrit_query=a_sa_query)
    b_result = BResult(response=b_full, chunks=b_chunks)

    final = await run_reflection_agent(pipeline_q, seeker_profile, a_result, b_result)

    # Stream reflection reasoning — JSON-encoded, goes ONLY to ThinkingPanel.
    # This may contain error markers (e.g. "Reflection error ...") — that is fine
    # HERE because it never touches the final_response event.
    reasoning = final.reasoning or ""
    if reasoning:
        yield sse_json("reflection_reasoning", reasoning)

    # Step 8: Stream final response in ~word-sized chunks for smooth appearance.
    # Each piece is JSON-encoded so spaces AND newlines (paragraph breaks)
    # survive SSE framing intact — the SSE \n\n terminator can't corrupt it.
    final_text = final.final_response or ""
    if not final_text.strip():
        # Never leave the response area empty — give a graceful line.
        final_text = "The retrieved passages did not yield a grounded answer for this question. Please rephrase or ask about a related teaching."
    if final_text:
        # Split on whitespace runs but KEEP the separators so spacing is exact
        import re as _re
        tokens = _re.split(r"(\s+)", final_text)  # ['The',' ','retrieved',' ',...]
        # Regroup into ~4-word pieces, separators included
        piece = ""
        word_count = 0
        for tok in tokens:
            piece += tok
            if tok and not tok.isspace():
                word_count += 1
            if word_count >= 4:
                yield sse_json("final_response", piece)
                piece = ""
                word_count = 0
        if piece:
            yield sse_json("final_response", piece)

    # Step 9: Done
    session_id = str(uuid.uuid4())
    yield sse("done", {
        "session_id": session_id,
        "chunks_used": [
            {
                "text_name": c.get("text_name"),
                "verse_number": c.get("verse_number"),
                "content": c.get("content"),
                "authenticity": c.get("authenticity"),
                "similarity": round(c.get("similarity", 0), 3),
            }
            for c in (final.chunks_used or [])
        ],
        "agent_a_response": a_full,
        "agent_b_response": b_full,
        "reflection_reasoning": reasoning,
        "reflection_winner": final.winner,
        "seeker_profile": {
            "level": seeker_profile.get("level"),
            "intent": seeker_profile.get("intent"),
            "language": seeker_profile.get("language"),
            "emotional_tone": seeker_profile.get("emotional_tone"),
        },
        "original_question": question,
        "translated_question": pipeline_q if pipeline_q != question else None,
    })


@router.post("/api/query/stream")
async def query_stream(request: StreamRequest, http_request: Request):
    client_ip = http_request.client.host if http_request.client else "unknown"
    # X-Forwarded-For from Render/proxy
    forwarded = http_request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    history = [{"role": m.role, "content": m.content} for m in (request.history or [])]
    total_chars = sum(len(m["content"]) for m in history)
    if total_chars > 12000:
        async def _too_long():
            yield sse("rate_limited", {
                "message": "This conversation has grown too long for a single session. Please start a new inquiry — your past darśanas are saved in My Darśanas.",
                "reset_at": None,
            })
        return StreamingResponse(_too_long(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return StreamingResponse(
        generate_stream(request.question, request.user_id, client_ip, history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
