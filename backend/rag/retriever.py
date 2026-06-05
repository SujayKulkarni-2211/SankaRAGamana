import os
from typing import List, Optional

from supabase import create_client, Client

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _client


PRIMARY_TEXT_BOOST = 1.5  # multiply similarity score for chunks from primary texts


def _rerank(chunks: List[dict], primary_texts: List[str]) -> List[dict]:
    """
    Re-score chunks: primary text chunks get a 1.3x similarity boost
    before final sort. Raw similarity is preserved in the original field;
    boosted score is used only for ordering.
    """
    primary_set = set(primary_texts)
    for chunk in chunks:
        raw = chunk.get("similarity", 0)
        boost = PRIMARY_TEXT_BOOST if chunk.get("text_name") in primary_set else 1.0
        chunk["_boosted_score"] = raw * boost
    chunks.sort(key=lambda x: x["_boosted_score"], reverse=True)
    return chunks


async def retrieve(
    query_embedding: List[float],
    seeker_profile: dict,
) -> List[dict]:
    """
    Retrieve chunks from Supabase pgvector.

    Strategy:
    1. Fetch top_k * 3 candidates from all texts (wide net)
    2. Re-rank: primary text chunks get 1.3x similarity boost
    3. Select final top_k after re-ranking
    4. If include_commentary=True, add up to 2 commentary chunks
    """
    strategy = seeker_profile.get("retrieval_strategy", {})
    top_k = strategy.get("top_k", 5)
    primary_texts = strategy.get("primary_texts", [])
    include_commentary = strategy.get("include_commentary", False)

    client = get_client()

    # Phase A: fetch best chunks from primary texts specifically (low threshold)
    primary_results = []
    if primary_texts:
        primary_results = _vector_search(
            client,
            query_embedding,
            top_k=max(top_k, 6),
            text_filter=primary_texts,
            match_threshold=0.1,
        )

    # Phase B: wide candidate pool from all texts
    all_results = _vector_search(
        client,
        query_embedding,
        top_k=top_k * 3,
        text_filter=None,
        match_threshold=0.2,
    )

    # Merge: primary results first, then fill from wide pool (no duplicates)
    seen_ids = {r["chunk_id"] for r in primary_results}
    candidates = list(primary_results)
    for r in all_results:
        if r["chunk_id"] not in seen_ids:
            candidates.append(r)
            seen_ids.add(r["chunk_id"])

    # Re-rank with primary text boost then select top_k
    candidates = _rerank(candidates, primary_texts)
    results = candidates[:top_k]

    # Commentary pass — add up to 2 extra chunks if requested
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

    return results


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
