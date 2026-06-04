"""
Generates/updates corpus/tracker.json from corpus/chunks/ data.
Also syncs to Supabase corpus_tracker table.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

CHUNKS_DIR = Path("corpus/chunks")
TRACKER_PATH = Path("corpus/tracker.json")
LOG_DIR = Path("logs")


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


def build_tracker() -> dict:
    now = datetime.utcnow().isoformat()
    texts = []
    total_chunks = 0

    for chunk_file in sorted(CHUNKS_DIR.glob("*_chunks.json")):
        chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
        if not chunks:
            continue
        sample = chunks[0]
        entry = {
            "text_name": sample["text_name"],
            "title_devanagari": sample.get("text_title_devanagari", ""),
            "category": sample.get("category", ""),
            "authenticity": sample.get("authenticity", "attributed"),
            "source": sample.get("source", ""),
            "chunk_count": len(chunks),
            "status": "ingested",
            "last_updated": now,
        }
        texts.append(entry)
        total_chunks += len(chunks)

    return {
        "last_updated": now,
        "total_texts": len(texts),
        "total_chunks": total_chunks,
        "texts": texts,
    }


def sync_to_supabase(tracker: dict):
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        logging.warning("Supabase credentials not set — skipping sync")
        return

    client = create_client(supabase_url, supabase_key)
    rows = [
        {
            "text_name": t["text_name"],
            "text_title_devanagari": t["title_devanagari"],
            "category": t["category"],
            "authenticity": t["authenticity"],
            "source": t["source"],
            "chunk_count": t["chunk_count"],
            "status": t["status"],
            "last_updated": t["last_updated"],
        }
        for t in tracker["texts"]
    ]
    for row in rows:
        client.table("corpus_tracker").upsert(row, on_conflict="text_name").execute()
    logging.info(f"Synced {len(rows)} entries to corpus_tracker")


def main():
    setup_logging()

    if not CHUNKS_DIR.exists():
        print(f"chunks dir not found: {CHUNKS_DIR}")
        return

    tracker = build_tracker()
    TRACKER_PATH.write_text(json.dumps(tracker, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"tracker.json updated: {tracker['total_texts']} texts, {tracker['total_chunks']} chunks")

    sync_to_supabase(tracker)
    print("Synced to Supabase corpus_tracker")


if __name__ == "__main__":
    main()
