import os
import json
import math
from pathlib import Path
from typing import List, Optional, Dict

from supabase import create_client, Client

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _client


# ── Book centroids ──────────────────────────────────────────────────────────
# Each book has an average (L2-normalised) embedding. Comparing the query to a
# book's centroid tells us whether that book is GENUINELY about the topic, vs.
# merely having a few locally-similar chunks. This lets us tell apart honest
# domination ("this book really is about this") from lazy/volume flooding.
_CENTROIDS_PATH = Path(__file__).parent / "data" / "book_centroids.json"
_centroids: Optional[Dict[str, list]] = None


def _load_centroids() -> Dict[str, list]:
    global _centroids
    if _centroids is None:
        _centroids = {}
        try:
            raw = json.loads(_CENTROIDS_PATH.read_text())
            _centroids = {tn: d["centroid"] for tn, d in raw.items()}
        except Exception as e:
            print(f"[retriever] could not load book centroids: {e}")
            _centroids = {}
    return _centroids


def _book_similarity(query_embedding: List[float], text_name: str) -> float:
    """Cosine similarity between query and a book's centroid (0 if unknown).
    query_embedding need not be normalised; centroids already are."""
    cents = _load_centroids()
    c = cents.get(text_name)
    if not c:
        return 0.0
    dot = sum(q * v for q, v in zip(query_embedding, c))
    qnorm = math.sqrt(sum(q * q for q in query_embedding)) or 1.0
    return dot / qnorm


# How many chunks the agents finally see. A paṇḍita draws on several sources,
# explains each, and shows how to apply them — so we retrieve generously.
FINAL_K = 10
CANDIDATE_POOL = 40  # wide net before diversity-aware selection

# Soft diversity, modulated by whether a book is GENUINELY on-topic.
# Each additional chunk from an already-picked text is discounted — but the
# size of that discount depends on the book's centroid similarity to the query:
#   - book genuinely about this (high centroid sim) → SMALL decay, it may keep
#     many slots (honest domination, like a paṇḍita citing the right text often)
#   - book just has locally-similar chunks (low centroid sim) → LARGE decay,
#     pushed aside so other works surface (this is the "lazy retrieval" guard)
DIVERSITY_DECAY_MAX = 0.05   # penalty per prior chunk when book is OFF-topic
DIVERSITY_DECAY_MIN = 0.008  # penalty per prior chunk when book is ON-topic
# Centroid-sim range over which decay interpolates from MAX→MIN.
CENTROID_LOW = 0.74
CENTROID_HIGH = 0.84

# The Gītā Bhāṣya is the universal text — "what is not in the Gītā is nowhere."
# A small standing boost so at least one Gītā passage tends to earn a seat in
# most answers, without letting it crowd out the genuinely closest sources.
GITA_TEXT = "gitabhashya"
GITA_BOOST = 0.012


def _book_decay(book_sim: float) -> float:
    """Interpolate per-source decay from MAX (off-topic) to MIN (on-topic)."""
    if book_sim <= CENTROID_LOW:
        return DIVERSITY_DECAY_MAX
    if book_sim >= CENTROID_HIGH:
        return DIVERSITY_DECAY_MIN
    frac = (book_sim - CENTROID_LOW) / (CENTROID_HIGH - CENTROID_LOW)
    return DIVERSITY_DECAY_MAX - frac * (DIVERSITY_DECAY_MAX - DIVERSITY_DECAY_MIN)


def _diversity_select(candidates: List[dict], k: int, query_embedding: List[float]) -> List[dict]:
    """
    Greedy selection: prefer high similarity, but discount repeated sources by
    an amount that depends on how genuinely on-topic each book is (its centroid
    similarity to the query). Honest domination is allowed; volume flooding and
    lazy clustering are not. The Gītā Bhāṣya gets a small universal-text boost.
    """
    # Precompute book-level centroid similarity for the texts present.
    book_sim: dict = {}
    for c in candidates:
        tn = c.get("text_name")
        if tn not in book_sim:
            book_sim[tn] = _book_similarity(query_embedding, tn)

    chosen: List[dict] = []
    per_text_count: dict = {}
    pool = list(candidates)

    while pool and len(chosen) < k:
        best, best_score, best_i = None, -1e9, -1
        for i, c in enumerate(pool):
            tn = c.get("text_name")
            sim = c.get("similarity", 0)
            seen = per_text_count.get(tn, 0)
            decay = _book_decay(book_sim.get(tn, 0.0))
            adjusted = sim - decay * seen
            if tn == GITA_TEXT:
                adjusted += GITA_BOOST
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

    results = _diversity_select(candidates, k, query_embedding)

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
