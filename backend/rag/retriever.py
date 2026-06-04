import os
from typing import List, Optional

from supabase import create_client, Client

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _client


async def retrieve(
    query_embedding: List[float],
    top_k: int = 5,
    authenticity_filter: Optional[str] = None,
) -> list:
    # TODO: implement in Step 4
    # Calls Supabase RPC match_corpus_chunks (pgvector cosine similarity)
    # Filters by authenticity if specified; prefers confirmed > attributed
    pass
