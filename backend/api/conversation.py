import os
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from supabase import create_client

router = APIRouter()
_db = None


def _get_db():
    global _db
    if _db is None:
        _db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _db


class SaveRequest(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    query: str
    final_response: str
    agent_a_response: Optional[str] = None
    agent_b_response: Optional[str] = None
    reflection_reasoning: Optional[str] = None
    chunks_used: Optional[list] = None
    seeker_profile: Optional[dict] = None
    language: Optional[str] = None


@router.post("/api/conversation/save")
async def save_conversation(req: SaveRequest):
    _get_db().table("conversations").upsert({
        "session_id": req.session_id,
        "user_id": req.user_id,
        "query": req.query,
        "final_response": req.final_response,
        "agent_a_response": req.agent_a_response,
        "agent_b_response": req.agent_b_response,
        "reflection_reasoning": req.reflection_reasoning,
        "chunks_used": req.chunks_used,
        "seeker_profile": req.seeker_profile,
        "language": req.language,
    }, on_conflict="session_id").execute()
    return {"session_id": req.session_id}


@router.get("/api/conversation/{session_id}")
async def get_conversation(session_id: str):
    result = _get_db().table("conversations").select("*").eq(
        "session_id", session_id
    ).limit(1).execute()
    if not result.data:
        return None
    return result.data[0]


@router.get("/api/conversations/history")
async def get_history(user_id: str, limit: int = 50):
    result = _get_db().table("conversations").select(
        "session_id, query, language, created_at"
    ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return result.data
