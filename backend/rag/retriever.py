import os
from typing import List, Optional, Dict

from supabase import create_client, Client

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    return _client


# ── Book centroids (in Supabase) ────────────────────────────────────────────
# Each book has an average embedding (its centroid) stored in the book_centroids
# table and refreshed in-database from corpus_chunks. Comparing the query to a
# book's centroid tells us whether the book is GENUINELY about the topic vs.
# merely having a few locally-similar chunks — distinguishing honest domination
# from lazy/volume flooding.
#
# Scalable: add/remove/re-embed texts, then `select refresh_book_centroids();`
# and every book's centroid is recomputed in the DB. No app-side state.
def _fetch_book_similarities(query_embedding: List[float]) -> Dict[str, float]:
    """One RPC call returns cosine similarity of the query to EVERY book's
    centroid. Returns {} on failure so retrieval degrades gracefully."""
    try:
        resp = get_client().rpc(
            "match_book_centroids", {"query_embedding": query_embedding}
        ).execute()
        return {row["text_name"]: row["similarity"] for row in (resp.data or [])}
    except Exception as e:
        print(f"[retriever] match_book_centroids failed: {e}")
        return {}


# How many chunks the agents finally see. A paṇḍita draws on several sources,
# explains each, and shows how to apply them — so we retrieve generously.
# Raised from 10 → 16 so a book that is genuinely ABOUT the topic can contribute
# many of its verses (depth), while off-topic books still appear (breadth).
FINAL_K = 10   # fits the free-tier per-minute token budget (8k TPM on the
               # current heavy model). Depth-aware selection (below) still lets
               # an on-topic book take several of these 10 slots.
CANDIDATE_POOL = 50  # wide net before selection, so on-topic books have enough
                     # verses available for _depth_select to go deep.

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


PRIMARY_BOOST = 0.06  # boost for texts the profiler explicitly named (deity/topic)


def _diversity_select(candidates: List[dict], k: int, book_sim: Dict[str, float],
                      primary_texts: Optional[set] = None) -> List[dict]:
    """
    Greedy selection: prefer high similarity, but discount repeated sources by
    an amount that depends on how genuinely on-topic each book is (its centroid
    similarity to the query, from book_sim). Honest domination is allowed;
    volume flooding and lazy clustering are not. The Gītā gets a small boost.
    """
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
            if primary_texts and tn in primary_texts:
                adjusted += PRIMARY_BOOST
            if adjusted > best_score:
                best, best_score, best_i = c, adjusted, i
        chosen.append(best)
        per_text_count[best.get("text_name")] = per_text_count.get(best.get("text_name"), 0) + 1
        pool.pop(best_i)

    return chosen


# ── Depth-aware selection: a book WRITTEN ABOUT the topic may contribute many
# verses; an off-topic book gets a token presence. The per-book cap scales with
# the book's centroid similarity to the query (how genuinely on-topic it is).
# This fixes the old 1-verse-per-book flattening that crippled deep answers when
# an entire text bears on the question (e.g. a whole prakaraṇa on māyā, or the
# Gītā Bhāṣya on karma-yoga). Breadth is still preserved for off-topic books.
def _book_cap(book_sim: float) -> int:
    if book_sim >= 0.84: return 6   # genuinely about it → go deep
    if book_sim >= 0.82: return 4
    if book_sim >= 0.80: return 3
    if book_sim >= 0.78: return 2
    return 1                        # off-topic → one verse, for breadth


def _depth_select(candidates: List[dict], k: int, book_sim: Dict[str, float],
                  primary_texts: Optional[set] = None) -> List[dict]:
    """Take highest-similarity chunks first, but never exceed a book's
    centroid-scaled cap. Named texts (deity/topic overrides) get +1 headroom."""
    primary = primary_texts or set()
    chosen: List[dict] = []
    per: dict = {}
    for c in sorted(candidates, key=lambda x: -x.get("similarity", 0)):
        if len(chosen) >= k:
            break
        tn = c.get("text_name")
        cap = _book_cap(book_sim.get(tn, 0.0))
        if tn in primary:
            cap += 1
        if per.get(tn, 0) < cap:
            chosen.append(c)
            per[tn] = per.get(tn, 0) + 1
    # If caps left us short of k (rare), backfill by pure similarity.
    if len(chosen) < k:
        taken = {id(c) for c in chosen}
        for c in sorted(candidates, key=lambda x: -x.get("similarity", 0)):
            if len(chosen) >= k:
                break
            if id(c) not in taken:
                chosen.append(c)
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
    # Texts the profiler explicitly named (deity/topic overrides). NOT a filter —
    # we fetch their best chunks into the pool and give them a boost so niche
    # texts (e.g. a deity stotra) can surface where pure similarity misses them.
    primary_texts = set(strategy.get("primary_texts", []))

    client = get_client()

    candidates = _vector_search(
        client,
        query_embedding,
        top_k=CANDIDATE_POOL,
        text_filter=None,
        match_threshold=0.0,
    )

    # Ensure named texts have candidates in the pool (a boost can't lift what
    # isn't there). Fetch their best chunks specifically and merge in.
    if primary_texts:
        seen = {c.get("chunk_id") for c in candidates}
        extra = _vector_search(
            client, query_embedding, top_k=4,
            text_filter=list(primary_texts), match_threshold=0.0,
        )
        for c in extra:
            if c.get("chunk_id") not in seen:
                candidates.append(c)
                seen.add(c.get("chunk_id"))

    # One RPC: query-vs-every-book centroid similarity (the laziness signal).
    # Stored in Supabase (book_centroids table) so adding/re-embedding texts +
    # refresh_book_centroids() keeps it in sync — no app-side recompute.
    book_sim = _fetch_book_similarities(query_embedding)

    # Depth-aware: on-topic books may go deep (many verses), off-topic books get
    # one — so a text written about the question is summarised richly, not
    # flattened to a single line. (_diversity_select is kept as the older
    # one-per-book strategy for reference/fallback.)
    results = _depth_select(candidates, k, book_sim, primary_texts)

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
