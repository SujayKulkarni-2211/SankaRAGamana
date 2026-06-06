-- Book centroids in Supabase (pgvector) — scalable replacement for the local
-- JSON file. Centroids are AVERAGED FROM corpus_chunks inside the database, so
-- adding/removing/re-embedding texts and calling refresh_book_centroids() keeps
-- everything in sync with no app-side recompute.

-- 1. The table
create table if not exists book_centroids (
  text_name   text primary key,
  centroid    vector(1024) not null,
  n_chunks    integer not null,
  updated_at  timestamptz not null default now()
);

-- 2. Recompute all centroids from corpus_chunks.
--    AVG(embedding) over a text, then we rely on cosine distance at query time
--    (pgvector's <=> normalises internally for cosine), so storing the raw mean
--    is fine. Call this after any corpus change.
create or replace function refresh_book_centroids()
returns integer
language plpgsql
as $$
declare
  n integer;
begin
  delete from book_centroids;
  insert into book_centroids (text_name, centroid, n_chunks, updated_at)
  select
    text_name,
    avg(embedding)::vector(1024) as centroid,
    count(*)                     as n_chunks,
    now()
  from corpus_chunks
  group by text_name;
  get diagnostics n = row_count;
  return n;
end;
$$;

-- 3. Query-vs-centroid similarity for every book, returned cheaply.
--    Uses cosine distance (<=>); similarity = 1 - distance.
create or replace function match_book_centroids(query_embedding vector(1024))
returns table (text_name text, similarity float, n_chunks integer)
language sql stable
as $$
  select
    text_name,
    1 - (centroid <=> query_embedding) as similarity,
    n_chunks
  from book_centroids
$$;

-- 4. Populate now.
select refresh_book_centroids();
