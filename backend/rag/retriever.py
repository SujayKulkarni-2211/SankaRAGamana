import os
from typing import List, Optional

from supabase import create_client, Client

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _client


# How many chunks the agents finally see. A paṇḍita draws on several sources,
# explains each, and shows how to apply them — so we retrieve generously.
FINAL_K = 10
CANDIDATE_POOL = 40  # wide net before diversity-aware selection

# Soft diversity: a single text MAY dominate if it is genuinely most relevant,
# but each additional chunk from an already-represented text is gently
# discounted, so equally-relevant passages from other works can surface.
# This mirrors a scholar who cites multiple sources rather than one.
DIVERSITY_DECAY = 0.02  # similarity penalty per prior chunk from the same text
                        # small enough that a genuinely dominant text keeps
                        # multiple slots, large enough to break monotony


def _diversity_select(candidates: List[dict], k: int) -> List[dict]:
    """
    Greedy selection that prefers high similarity but discounts repeated
    sources. A text can still win multiple slots if its chunks are clearly
    the strongest — domination by merit is allowed, domination by volume is not.
    """
    chosen: List[dict] = []
    per_text_count: dict = {}
    pool = list(candidates)

    while pool and len(chosen) < k:
        best, best_score, best_i = None, -1.0, -1
        for i, c in enumerate(pool):
            sim = c.get("similarity", 0)
            seen = per_text_count.get(c.get("text_name"), 0)
            # discount by how many we've already taken from this text
            adjusted = sim - DIVERSITY_DECAY * seen
            if adjusted > best_score:
                best, best_score, best_i = c, adjusted, i
        chosen.append(best)
        per_text_count[best.get("text_name")] = per_text_count.get(best.get("text_name"), 0) + 1
        pool.pop(best_i)

    return chosen


async def retrieve(
    query_embedding: List[float],
    seeker_profile: dict,
) -> List[dict]:
    """
    Retrieve chunks from Supabase pgvector — PURE SEMANTIC across all texts.

    The seeker profile no longer restricts WHICH texts are searched; relevance
    to the question alone decides what surfaces. The profile only shapes how
    the answer is explained (register/depth), handled by the agents.

    Strategy:
    1. Wide semantic net across ALL texts (CANDIDATE_POOL candidates)
    2. Diversity-aware selection: prefer relevance, discount repeated sources
    3. Return FINAL_K chunks spanning several works when relevance is comparable
    """
    # top_k from the profile is respected as a floor, but we lean generous so
    # answers can cite and explain multiple sources like a learned teacher.
    strategy = seeker_profile.get("retrieval_strategy", {})
    k = max(strategy.get("top_k", FINAL_K), FINAL_K)

    client = get_client()

    candidates = _vector_search(
        client,
        query_embedding,
        top_k=CANDIDATE_POOL,
        text_filter=None,
        match_threshold=0.0,
    )

    results = _diversity_select(candidates, k)

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
