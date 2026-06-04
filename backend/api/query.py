from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.rag.embedder import Embedder
from backend.rag.seeker_profiler import profile_seeker
from backend.rag.retriever import retrieve
from backend.rag.generator import generate

router = APIRouter()

embedder = Embedder()


class QueryRequest(BaseModel):
    question: str


@router.post("/api/query")
async def query(request: QueryRequest):
    question = request.question.strip()

    # Step 1: Profile the seeker (~0.5s, transforms response quality)
    seeker_profile = await profile_seeker(question)

    # Step 2: Embed query with "query: " prefix (non-negotiable for e5)
    query_embedding = embedder.embed_query(question)

    # Step 3: Retrieve — seeker_profile drives which texts and how many
    chunks = await retrieve(query_embedding, seeker_profile)

    # Step 4: Generate — Shankara responds as Guru, meeting seeker where they are
    answer = await generate(question, chunks, seeker_profile)

    return {
        "answer": answer,
        "seeker_profile": {
            "level": seeker_profile.get("level"),
            "intent": seeker_profile.get("intent"),
            "language": seeker_profile.get("language"),
            "emotional_tone": seeker_profile.get("emotional_tone"),
        },
        "sources": [
            {
                "text_name": c.get("text_name"),
                "verse_number": c.get("verse_number"),
                "content": c.get("content"),
                "authenticity": c.get("authenticity"),
                "similarity": round(c.get("similarity", 0), 3),
            }
            for c in chunks
        ],
    }
