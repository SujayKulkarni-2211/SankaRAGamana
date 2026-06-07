"""
Rate limiting — two levels:
  1. Per-identifier: anonymous=5/hr (by IP), logged_in=15/hr (by user_id)
  2. Global: 500/day across all users

Uses Supabase directly via psycopg2 for atomic upsert+increment.
Supabase REST client doesn't support atomic increments safely.
"""

import os
import psycopg2
import psycopg2.pool
from datetime import datetime, timedelta
from typing import Optional, Tuple

_pool: Optional[psycopg2.pool.SimpleConnectionPool] = None

# Token budget: 3 Groq free keys × 100K tokens/day = 300K/day.
# Each query ≈ 3,600 tokens (profiler + agent A + agent B + reflection).
# 150 queries/day × 3,600 = 540K — tight but workable with 3 keys rotating.
# Individual limits are squeezed to distribute the pool fairly across users.
ANON_LIMIT   = 1    # 1/hr per IP — server-enforced, no bypass possible
USER_LIMIT   = 3    # 3/hr per signed-in user (one focused session)
GLOBAL_DAILY = 150  # hard daily ceiling — ~50 users × 3 questions

RATE_LIMITED_MESSAGE = (
    "You have reached the limit for this period. "
    "SankaRĀGamana tracks usage by your network address — "
    "opening new tabs or clearing your browser will not change this. "
    "If you are not signed in, sign in with Google to continue "
    "(signed-in seekers receive 3 questions per hour). "
    "If you are signed in, please return in an hour. "
    "The service is free. We simply need to keep it available to all seekers equally."
)

GLOBAL_LIMITED_MESSAGE = (
    "SankaRĀGamana has reached its daily capacity. "
    "The service will resume tomorrow. "
    "We do not monetize this service — these limits exist to keep it "
    "freely available. "
    "The complete source code is on GitHub if you wish to run your own instance."
)

# Shown when the underlying free LLM provider (Groq / Llama) has exhausted its
# daily token allowance — a limit of the free infrastructure, not of the corpus.
LLM_EXHAUSTED_MESSAGE = (
    "SankaRĀGamana runs entirely on free resources so it can stay free for every "
    "seeker. Its language provider — Groq, serving the Llama model — has a daily "
    "free-tier token allowance, and that allowance has been spent for today. "
    "This is a limit of the free infrastructure, nothing more. The allowance "
    "renews at midnight UTC (around 5:30 AM IST); please return then. "
    "The full source is on GitHub if you wish to run your own instance with your own keys."
)


def _get_pool() -> psycopg2.pool.SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            1, 5,
            host="db.srjbwyixtqdcqjcfmrwd.supabase.co",
            port=5432,
            dbname="postgres",
            user="postgres",
            password=os.getenv("DB_PASSWORD", "brahmasatyamjaganmithya@rag"),
        )
    return _pool


async def check_rate_limits(
    user_id: Optional[str],
    client_ip: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Returns (allowed, message, reset_at_iso).
    reset_at_iso is the ISO timestamp when the window resets.
    """
    identifier = user_id if user_id else client_ip
    id_type = "user" if user_id else "ip"
    limit = USER_LIMIT if user_id else ANON_LIMIT

    # Acquiring the DB connection must NEVER crash the request. The direct
    # Postgres connection can fail in restricted hosts (e.g. IPv6-only direct
    # endpoint); if so, fail OPEN — skip rate limiting rather than kill the
    # stream. (The whole point of rate-limiting is moot if the app is down.)
    try:
        pool = _get_pool()
        conn = pool.getconn()
    except Exception as e:
        print(f"[rate_limit] pool/connection unavailable, skipping limit: {e}")
        return True, None, None
    try:
        conn.autocommit = False
        cur = conn.cursor()

        # --- Per-user check ---
        # Upsert: create row if not exists, reset window if expired
        cur.execute("""
            INSERT INTO rate_limits (identifier, identifier_type, query_count, window_start)
            VALUES (%s, %s, 0, NOW())
            ON CONFLICT (identifier, identifier_type)
            DO UPDATE SET
                query_count = CASE
                    WHEN rate_limits.window_start < NOW() - INTERVAL '1 hour'
                    THEN 0
                    ELSE rate_limits.query_count
                END,
                window_start = CASE
                    WHEN rate_limits.window_start < NOW() - INTERVAL '1 hour'
                    THEN NOW()
                    ELSE rate_limits.window_start
                END
            RETURNING query_count, window_start;
        """, (identifier, id_type))
        row = cur.fetchone()
        current_count = row[0]
        window_start = row[1]
        reset_at = (window_start + timedelta(hours=1)).isoformat()

        if current_count >= limit:
            conn.rollback()
            return False, RATE_LIMITED_MESSAGE, reset_at

        # --- Global check ---
        cur.execute("""
            UPDATE global_rate_limit SET
                query_count = CASE
                    WHEN window_start < NOW() - INTERVAL '24 hours'
                    THEN 1
                    ELSE query_count + 1
                END,
                window_start = CASE
                    WHEN window_start < NOW() - INTERVAL '24 hours'
                    THEN NOW()
                    ELSE window_start
                END
            WHERE id = 1
            RETURNING query_count, window_start;
        """)
        g_row = cur.fetchone()
        global_count = g_row[0]
        global_window_start = g_row[1]
        global_reset_at = (global_window_start + timedelta(hours=24)).isoformat()

        if global_count > GLOBAL_DAILY:
            conn.rollback()
            return False, GLOBAL_LIMITED_MESSAGE, global_reset_at

        # --- Increment user count ---
        cur.execute("""
            UPDATE rate_limits
            SET query_count = query_count + 1
            WHERE identifier = %s AND identifier_type = %s;
        """, (identifier, id_type))

        conn.commit()
        return True, None, None

    except Exception as e:
        conn.rollback()
        print(f"[rate_limit] error: {e}")
        return True, None, None  # fail open — don't block on DB error
    finally:
        cur.close()
        pool.putconn(conn)
