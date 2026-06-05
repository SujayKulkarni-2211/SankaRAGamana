"""
Groq client factory with round-robin key rotation.

Three API keys are rotated so concurrent agent calls
(Agent A, Agent B, Reflection) each use a different key,
tripling the effective per-minute token budget.
"""

import os
import threading
from groq import Groq

_lock = threading.Lock()
_index = 0
_clients: list[Groq] = []


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


def get_client() -> Groq:
    """Return the next Groq client in round-robin order."""
    global _index
    if not _clients:
        _init()
    with _lock:
        client = _clients[_index % len(_clients)]
        _index += 1
    return client
