-- Persistent seeker profile — the "sleep consolidation" memory.
--
-- One durable row per logged-in user, distilled OFFLINE (in the background) from
-- their accumulated conversations. A Guru remembers the seeker across visits:
-- their depth, what they keep returning to, the tongue they think in, the tone
-- that reaches them. This is NOT the per-query profile (that stays live and
-- ephemeral) — it is the slow, settled understanding the per-query profile is
-- blended WITH at retrieval time.

create table if not exists seeker_profiles (
  user_id              text primary key,

  -- distilled, durable signals
  level                text,          -- beginner|intermediate|advanced|scholar
  dominant_intent      text,          -- definitional|philosophical|personal|devotional|in_distress
  language             text,          -- en|sa|kn|hi
  tone                 text,          -- curious|distressed|devotional|analytical
  recurring_themes     text[] default '{}',   -- e.g. {atman, maya, suffering}
  affinity_texts       text[] default '{}',   -- texts that have served this seeker well
  notes                text,          -- one short paragraph: "who this seeker is"

  -- bookkeeping for the staleness check
  n_exchanges_seen     integer not null default 0,  -- exchanges folded in so far
  last_consolidated_at timestamptz,
  updated_at           timestamptz not null default now()
);

-- index for nothing fancy — primary key on user_id is enough — but keep an
-- updated_at index in case we ever want "stale users" sweeps.
create index if not exists seeker_profiles_consolidated_idx
  on seeker_profiles (last_consolidated_at);
