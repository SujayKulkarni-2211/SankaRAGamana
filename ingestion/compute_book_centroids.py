"""
Compute the average (L2-normalised) embedding per book — the book "centroid".

Used by the retriever to tell whether a book is GENUINELY about a query topic
(high centroid similarity) versus merely having a few locally-similar chunks
(low centroid similarity). This distinguishes honest domination from lazy
retrieval flooding.

Re-run this whenever the corpus changes (texts added/removed/re-embedded).
Output: backend/rag/data/book_centroids.json
"""

import os
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

OUT_PATH = Path("backend/rag/data/book_centroids.json")


def main():
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

    sums = defaultdict(lambda: None)
    counts = defaultdict(int)

    offset = 0
    while True:
        r = client.table("corpus_chunks").select("text_name,embedding").range(offset, offset + 499).execute()
        if not r.data:
            break
        for row in r.data:
            tn = row["text_name"]
            emb = row["embedding"]
            if isinstance(emb, str):
                emb = json.loads(emb)
            v = np.array(emb, dtype=np.float32)
            sums[tn] = v.copy() if sums[tn] is None else sums[tn] + v
            counts[tn] += 1
        offset += 500
        if len(r.data) < 500:
            break

    centroids = {}
    for tn in sums:
        centroid = sums[tn] / counts[tn]
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm  # normalise for cosine-as-dot-product
        centroids[tn] = {"centroid": centroid.tolist(), "n_chunks": counts[tn]}

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(centroids))
    print(f"Wrote {len(centroids)} book centroids → {OUT_PATH}")


if __name__ == "__main__":
    main()
