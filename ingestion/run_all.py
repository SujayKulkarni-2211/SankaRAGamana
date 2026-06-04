"""
Runs the full ingestion pipeline in order.
Step 1: scraper.py        — download .itx files
Step 2: gretil_fetcher.py — download GRETIL files
Step 3: converter.py      — ITRANS → Devanagari
Step 4: chunker.py        — split into verses/chunks
Step 5: embedder_local.py — embed + push to Supabase
Step 6: tracker.py        — update tracker.json + Supabase
"""

import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import scraper, gretil_fetcher, converter, chunker, embedder_local, tracker


def main():
    print("\n====== SankaRĀGamana Ingestion Pipeline ======\n")

    print("Step 1: Downloading from sanskritdocuments.org...")
    scraper.main()

    print("\nStep 2: Downloading from GRETIL...")
    gretil_fetcher.main()

    print("\nStep 3: Converting ITRANS → Devanagari...")
    converter.main()

    print("\nStep 4: Chunking texts...")
    chunker.main()

    print("\nStep 5: Embedding + pushing to Supabase...")
    embedder_local.main()

    print("\nStep 6: Updating tracker.json...")
    tracker.main()

    print("\n====== Pipeline complete ======")


if __name__ == "__main__":
    main()
