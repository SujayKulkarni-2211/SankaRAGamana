from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    authenticity_filter: Optional[str] = None  # 'confirmed' | 'attributed' | None


@router.post("/api/query")
async def query(request: QueryRequest):
    # TODO: implement in Step 4
    # 1. Embed query with "query: " prefix
    # 2. Retrieve top_k chunks from Supabase
    # 3. Prioritise confirmed > attributed
    # 4. Generate response with Groq
    # 5. Return answer + source citations + retrieved chunks
    pass
