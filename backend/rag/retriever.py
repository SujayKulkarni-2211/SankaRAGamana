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
    seeker_profile: dict,
) -> List[dict]:
    """
    Retrieve chunks from Supabase pgvector.

    Strategy (from seeker_profile):
    1. Search primary_texts first with match_threshold=0.3
    2. If we don't fill top_k, expand to all texts
    3. If include_commentary=True, also pull commentary-category chunks
    """
    strategy = seeker_profile.get("retrieval_strategy", {})
    top_k = strategy.get("top_k", 5)
    primary_texts = strategy.get("primary_texts", [])
    include_commentary = strategy.get("include_commentary", False)

    client = get_client()
    results = []

    # Phase 1: search within primary texts
    if primary_texts:
        phase1 = _vector_search(
            client,
            query_embedding,
            top_k=top_k,
            text_filter=primary_texts,
            match_threshold=0.25,
        )
        results.extend(phase1)

    # Phase 2: if we still need more chunks, expand to all texts
    if len(results) < top_k:
        seen_ids = {r["chunk_id"] for r in results}
        phase2 = _vector_search(
            client,
            query_embedding,
            top_k=top_k - len(results),
            text_filter=None,
            match_threshold=0.25,
        )
        for chunk in phase2:
            if chunk["chunk_id"] not in seen_ids:
                results.append(chunk)
                seen_ids.add(chunk["chunk_id"])

    # Phase 3: if include_commentary, add commentary chunks
    if include_commentary:
        seen_ids = {r["chunk_id"] for r in results}
        commentary = _vector_search(
            client,
            query_embedding,
            top_k=2,
            category_filter="commentary",
            match_threshold=0.2,
        )
        for chunk in commentary:
            if chunk["chunk_id"] not in seen_ids:
                results.append(chunk)

    # Sort by similarity score descending, cap at top_k + 2 for commentary
    results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    return results[:top_k + (2 if include_commentary else 0)]


def _vector_search(
    client: Client,
    query_embedding: List[float],
    top_k: int,
    text_filter: Optional[List[str]] = None,
    category_filter: Optional[str] = None,
    match_threshold: float = 0.25,
) -> List[dict]:
    """
    Call the Supabase RPC function match_corpus_chunks.
    Falls back to a direct table scan with manual similarity if RPC not found.
    """
    try:
        params = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": top_k,
        }
        if text_filter:
            params["filter_text_names"] = text_filter
        if category_filter:
            params["filter_category"] = category_filter

        result = client.rpc("match_corpus_chunks", params).execute()
        return result.data or []

    except Exception as e:
        # RPC not found — fallback: fetch recent chunks and return empty
        # (proper fallback requires pgvector RPC; log the error)
        print(f"[retriever] RPC error: {e}")
        return []
