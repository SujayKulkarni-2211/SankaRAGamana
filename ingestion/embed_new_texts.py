"""Embed only the two new bhashya texts and push to Supabase."""
import json
import os
import logging
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

NEW_TEXTS = [
    "gitabhashya_chunks.json",
    "brahmasutra_bhashya_chunks.json",
]


def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY not set in .env")
        return

    client = create_client(supabase_url, supabase_key)

    print("Loading multilingual-e5-large...")
    model = SentenceTransformer(
        "intfloat/multilingual-e5-large",
        device="cpu",
        cache_folder=os.getenv("MODEL_CACHE", "model_cache"),
    )
    print("Model ready\n")

    total = 0
    for fname in NEW_TEXTS:
        fpath = Path("corpus/chunks") / fname
        chunks = json.loads(fpath.read_text(encoding="utf-8"))
        text_name = chunks[0]["text_name"]
        print(f"=== {text_name}: {len(chunks)} chunks ===")

        texts = [f"passage: {c['content']}" for c in chunks]
        embeddings = model.encode(texts, batch_size=8, show_progress_bar=True)

        rows = [
            {
                "chunk_id": c["chunk_id"],
                "text_name": c["text_name"],
                "text_title_devanagari": c.get("text_title_devanagari", ""),
                "category": c.get("category", "bhashya"),
                "authenticity": c.get("authenticity", "primary"),
                "source": c.get("source", ""),
                "language": c.get("language", "sa"),
                "content": c["content"],
                "verse_number": c.get("verse_number", ""),
                "char_count": c.get("char_count", len(c["content"])),
                "embedding": emb.tolist(),
            }
            for c, emb in zip(chunks, embeddings)
        ]

        n_batches = (len(rows) + 99) // 100
        for i in range(0, len(rows), 100):
            batch = rows[i : i + 100]
            client.table("corpus_chunks").upsert(batch, on_conflict="chunk_id").execute()
            print(f"  Batch {i // 100 + 1}/{n_batches}: {len(batch)} rows upserted")

        total += len(rows)
        logging.info(f"Pushed {text_name}: {len(rows)} chunks")
        print()

    print(f"=== Done: {total} chunks pushed to Supabase ===")


if __name__ == "__main__":
    main()
