import asyncio
import uuid
from fastapi import APIRouter
from pydantic import BaseModel

from backend.rag.seeker_profiler import profile_seeker
from backend.rag.translator import translate_query_to_english
from backend.rag.agent_a import run_agent_a
from backend.rag.agent_b import run_agent_b
from backend.rag.reflection import run_reflection_agent

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/api/query")
async def query(request: QueryRequest):
    question = request.question.strip()

    # Step 1: Profile the seeker
    seeker_profile = await profile_seeker(question)

    # Step 2: Translate inbound query to English for Agent B if kn/hi
    # Agent A always translates to Sanskrit itself
    language = seeker_profile.get("language", "en")
    pipeline_question = await translate_query_to_english(question, language)

    # Step 3: Run Agent A (Sanskrit path) and Agent B (original language) in parallel
    agent_a_result, agent_b_result = await asyncio.gather(
        run_agent_a(pipeline_question, seeker_profile),
        run_agent_b(pipeline_question, seeker_profile),
    )

    # Step 4: Reflection agent judges both, retries if needed, outputs final
    final = await run_reflection_agent(
        query=pipeline_question,
        seeker_profile=seeker_profile,
        agent_a=agent_a_result,
        agent_b=agent_b_result,
    )

    session_id = str(uuid.uuid4())

    return {
        "response": final.final_response,
        "session_id": session_id,
        "agent_a_response": final.agent_a_response,
        "agent_b_response": final.agent_b_response,
        "reflection_reasoning": final.reasoning,
        "reflection_winner": final.winner,
        "chunks": [
            {
                "text_name": c.get("text_name"),
                "verse_number": c.get("verse_number"),
                "content": c.get("content"),
                "authenticity": c.get("authenticity"),
                "similarity": round(c.get("similarity", 0), 3),
            }
            for c in (final.chunks_used or [])
        ],
        "seeker_profile": {
            "level": seeker_profile.get("level"),
            "intent": seeker_profile.get("intent"),
            "language": seeker_profile.get("language"),
            "emotional_tone": seeker_profile.get("emotional_tone"),
        },
        "original_question": question,
        "translated_question": pipeline_question if pipeline_question != question else None,
    }
