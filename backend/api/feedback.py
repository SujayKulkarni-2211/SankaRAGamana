import os
from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel
from supabase import create_client

from backend.rag.imprints import distill_negative, maybe_distill_positive

router = APIRouter()
_db = None


def _get_db():
    global _db
    if _db is None:
        _db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _db


class FeedbackRequest(BaseModel):
    session_id: str
    query: str
    final_response: str
    agent_a_response: Optional[str] = None
    agent_b_response: Optional[str] = None
    reflection_reasoning: Optional[str] = None
    chunks_used: Optional[List[dict]] = None
    rating: bool
    feedback_text: Optional[str] = None
    language: Optional[str] = None
    seeker_level: Optional[str] = None


@router.post("/api/feedback")
async def feedback(req: FeedbackRequest):
    db = _get_db()

    # Store feedback
    db.table("feedback").insert({
        "session_id": req.session_id,
        "query": req.query,
        "final_response": req.final_response,
        "agent_a_response": req.agent_a_response,
        "agent_b_response": req.agent_b_response,
        "reflection_reasoning": req.reflection_reasoning,
        "chunks_used": req.chunks_used,
        "rating": req.rating,
        "feedback_text": req.feedback_text,
        "language": req.language,
        "seeker_level": req.seeker_level,
        "processed_for_imprints": False,
    }).execute()

    if not req.rating:
        # Negative feedback — distill immediately
        await distill_negative(
            query=req.query,
            response=req.final_response,
            feedback_text=req.feedback_text or "",
            chunks=req.chunks_used or [],
        )
        return {"status": "stored", "imprint": "negative_distilled"}

    # Positive feedback — check if distillation threshold reached
    await maybe_distill_positive()
    return {"status": "stored", "imprint": "pending_threshold"}
