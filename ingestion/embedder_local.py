"""
Runs on your Victus locally. Uses GPU if available.
Loads chunks from corpus/chunks/, embeds with e5-LARGE, pushes to Supabase.

Uses multilingual-e5-large (560MB) for ingestion — significantly better
Sanskrit-English bridging than e5-small. The backend (Render) still uses
e5-small for query-time embedding; the vector dimension stays 1024 for large.

CRITICAL: passage prefix "passage: " for all document embeddings.
NOTE: Supabase embedding column must be vector(1024) for e5-large.
      Run the migration SQL before first use if switching from e5-small.
"""

import json
import logging
import os
from pathlib import Path
from typing import List

import torch
from sentence_transformers import SentenceTransformer
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

CHUNKS_DIR = Path("corpus/chunks")
LOG_DIR = Path("logs")
BATCH_SIZE = 32


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "ingestion.log", mode="a"),
            logging.StreamHandler(),
        ],
    )


def load_model() -> SentenceTransformer:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading e5-large on {device}...")
    return SentenceTransformer(
        "intfloat/multilingual-e5-large",
        device=device,
        cache_folder=os.getenv("MODEL_CACHE", "model_cache"),
    )


def embed_chunks(model: SentenceTransformer, chunks: List[dict]) -> List[List[float]]:
    # CRITICAL: "passage: " prefix for documents
    texts = [f"passage: {c['content']}" for c in chunks]
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True)
    return embeddings.tolist()


def push_to_supabase(client, chunks: List[dict], embeddings: List[List[float]]):
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append(
            {
                "chunk_id": chunk["chunk_id"],
                "text_name": chunk["text_name"],
                "text_title_devanagari": chunk.get("text_title_devanagari", ""),
                "category": chunk.get("category", ""),
                "authenticity": chunk.get("authenticity", "attributed"),
                "source": chunk.get("source", ""),
                "language": chunk.get("language", "sa"),
                "content": chunk["content"],
                "verse_number": chunk.get("verse_number", ""),
                "char_count": chunk.get("char_count", len(chunk["content"])),
                "embedding": emb,
            }
        )

    # Upsert in batches of 100
    for i in range(0, len(rows), 100):
        batch = rows[i : i + 100]
        result = client.table("corpus_chunks").upsert(batch, on_conflict="chunk_id").execute()
        logging.info(f"  Upserted batch {i // 100 + 1}: {len(batch)} rows")


def main():
    setup_logging()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    client = create_client(supabase_url, supabase_key)
    model = load_model()

    chunk_files = list(CHUNKS_DIR.glob("*_chunks.json"))
    if not chunk_files:
        print(f"No chunk files found in {CHUNKS_DIR}")
        return

    # Test with 1 chunk before bulk insert
    print("\n--- Connection test: inserting 1 chunk ---")
    first_file = chunk_files[0]
    test_chunks = json.loads(first_file.read_text(encoding="utf-8"))[:1]
    test_embeddings = embed_chunks(model, test_chunks)
    push_to_supabase(client, test_chunks, test_embeddings)

    # Verify it's retrievable
    verify = (
        client.table("corpus_chunks")
        .select("chunk_id, text_name, char_count")
        .eq("chunk_id", test_chunks[0]["chunk_id"])
        .execute()
    )
    if verify.data:
        print(f"Connection test passed: {verify.data[0]}")
    else:
        print("ERROR: Test chunk not retrievable. Aborting bulk insert.")
        return

    # Bulk insert all
    total_embedded = 0
    for chunk_file in chunk_files:
        chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
        text_name = chunks[0]["text_name"] if chunks else chunk_file.stem
        print(f"\nEmbedding {text_name}: {len(chunks)} chunks...")
        embeddings = embed_chunks(model, chunks)
        push_to_supabase(client, chunks, embeddings)
        total_embedded += len(chunks)
        logging.info(f"Embedded and pushed {text_name}: {len(chunks)} chunks")

    print(f"\n=== embedder_local done: {total_embedded} chunks pushed to Supabase ===")


if __name__ == "__main__":
    main()
