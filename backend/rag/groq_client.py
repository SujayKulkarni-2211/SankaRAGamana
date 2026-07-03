"""
Groq client factory with round-robin key rotation AND daily-exhaustion failover.

Three API keys are rotated so concurrent agent calls (Agent A, Agent B,
Reflection) spread load across keys. When a key hits its daily token limit
(TPD 429), it is marked exhausted until the next UTC day so the rotation
stops handing it out — preventing the "one agent always fails" symptom.
"""

import os
import time
import threading
from datetime import datetime, timezone
from groq import Groq

# ── Models (env-configurable) ────────────────────────────────────────────────
# Groq deprecates models periodically (e.g. llama-3.3-70b-versatile → Aug 2026).
# Keep the model IDs in ONE place, overridable via env, so a decommission is a
# config change (set the env var + restart), never a code edit + redeploy.
#
#   MODEL_HEAVY — reasoning-grade: agents, reflection, synthesis, translation.
#   MODEL_LIGHT — fast/cheap: seeker profiler, memory distillation.
#
# Defaults follow Groq's current recommended replacements.
MODEL_HEAVY = os.getenv("GROQ_MODEL_HEAVY", "openai/gpt-oss-120b")
MODEL_LIGHT = os.getenv("GROQ_MODEL_LIGHT", "llama-3.1-8b-instant")

_lock = threading.Lock()
_index = 0
_clients: list[Groq] = []
# key index -> unix timestamp until which it is considered exhausted
_exhausted_until: dict[int, float] = {}


def _init():
    global _clients
    keys = [
        os.getenv("GROQ_API_KEY"),
        os.getenv("GROQ_API_KEY_2"),
        os.getenv("GROQ_API_KEY_3"),
    ]
    _clients = [Groq(api_key=k) for k in keys if k]
    if not _clients:
        raise RuntimeError("No GROQ_API_KEY set")


def _seconds_until_utc_midnight() -> float:
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # next midnight
    from datetime import timedelta
    tomorrow = tomorrow + timedelta(days=1)
    return (tomorrow - now).total_seconds()


def _live_indices() -> list[int]:
    """Indices of keys not currently marked exhausted."""
    now = time.time()
    return [i for i in range(len(_clients)) if _exhausted_until.get(i, 0) < now]


def _next_index() -> int:
    """Pick the next live key index (round-robin within the non-exhausted set)."""
    global _index
    if not _clients:
        _init()
    with _lock:
        live = _live_indices()
        if not live:
            live = list(range(len(_clients)))  # all dead — let caller get real error
        idx = live[_index % len(live)]
        _index += 1
    return idx


def get_client():
    """Return the next available Groq client, skipping exhausted keys.
    Backward-compatible: returns the client object directly."""
    return _clients[_next_index()]


def _mark_exhausted(key_index: int, retry_after_seconds: float | None = None):
    if retry_after_seconds is None:
        retry_after_seconds = _seconds_until_utc_midnight()
    with _lock:
        _exhausted_until[key_index] = time.time() + retry_after_seconds
    print(f"[groq] key #{key_index} marked exhausted for {int(retry_after_seconds)}s")


def chat(**kwargs):
    """Failover-aware chat completion. Tries each live key; on a daily-limit
    (TPD) 429, marks that key exhausted and retries with the next live key.
    Pass the same kwargs you would to client.chat.completions.create(...)."""
    if not _clients:
        _init()
    last_err = None
    tried = set()
    for _ in range(len(_clients)):
        idx = _next_index()
        if idx in tried:
            continue
        tried.add(idx)
        try:
            return _clients[idx].chat.completions.create(**kwargs)
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            # Daily token exhaustion → retire this key for the day, try next
            if "429" in msg and ("per day" in msg or "tpd" in msg or "tokens per day" in msg):
                _mark_exhausted(idx)
                continue
            # Other errors (per-minute, transient) → try next key once
            if "429" in msg:
                continue
            raise
    raise last_err


def any_key_available() -> bool:
    if not _clients:
        _init()
    return len(_live_indices()) > 0
