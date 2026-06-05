"""
Chunks the Bhagavad Gita Bhashya and Brahma Sutra Bhashya into
prose segments for embedding. Both are converted to Devanagari.

Bhashya prose has no ॥ — split on । and group 3-4 sentences per chunk.
Also produces chunks that combine sutra + bhashya for BSB.
"""

import json
import re
import logging
from pathlib import Path
from typing import List

CLEAN_DIR  = Path("corpus/clean/devanagari")
CHUNKS_DIR = Path("corpus/chunks")
LOG_DIR    = Path("logs")

MIN_CHARS = 40
MAX_CHARS = 600

BHASHYA_META = {
    "gitabhashya": {
        "text_name": "gitabhashya",
        "title_devanagari": "श्रीमद्भगवद्गीताशाङ्करभाष्यम्",
        "category": "bhashya",
        "authenticity": "primary",
        "source": "sanskritdocuments.org",
    },
    "brahmasutra_bhashya": {
        "text_name": "brahmasutra_bhashya",
        "title_devanagari": "ब्रह्मसूत्रशाङ्करभाष्यम्",
        "category": "bhashya",
        "authenticity": "primary",
        "source": "gretil.sub.uni-goettingen.de",
    },
}


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


def clean_itrans_artifacts(text: str) -> str:
    """Remove backslash joiners and encoding artifacts left by ITRANS converter."""
    # \\- word joiners (backslash-hyphen compound-word connector)
    text = text.replace('\\-', '')
    # backslash + Devanagari: \ldk \rdk etc that survived transliteration
    # Use explicit loop to avoid regex issues with Unicode after backslash
    import unicodedata
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text) and unicodedata.category(text[i+1]).startswith('L'):
            i += 1  # skip the backslash; the letter itself is also garbage (ldk/rdk artifact)
            # skip the following Devanagari cluster (ldk = ल्द्क़्)
            while i < len(text) and (unicodedata.category(text[i]).startswith('L') or text[i] in '़्'):
                i += 1
            continue
        result.append(text[i])
        i += 1
    text = ''.join(result)
    # Remove any remaining lone backslashes
    text = text.replace('\\', '')
    # Remove zero-width joiners and non-breaking spaces
    text = text.replace('\u200d', '').replace('\u200c', '').replace('\u00a0', ' ')
    return text


def clean_gretil_artifacts(text: str) -> str:
    """Remove GRETIL reference tags and section headers."""
    # Remove inline reference tags like |BBs_1,1.1| and their Devanagari equivalents
    # After IAST→Devanagari conversion BBs_1,1.1 becomes ब्ब्स्_१,१.१
    text = re.sub(r"ब्ब्स्_[\d,\.०-९]+", " ", text)
    text = re.sub(r"[|/]\s*[A-Z][A-Za-z_]+_[\d,\.]+\s*[|/]?", " ", text)
    # Also strip bare reference without pipes: ब्ब्स्_X,X.X pattern at sentence start
    text = re.sub(r"ब्ब्[^\s।॥]{0,15}", " ", text)
    # Remove lone forward-slash sentence terminators (GRETIL uses / instead of ।)
    # Only remove when surrounded by spaces or at line end
    text = re.sub(r"\s+/\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+/\s+", " ", text)
    # Remove lines that are purely section headers (no real prose/verse)
    lines = []
    for line in text.splitlines():
        s = line.strip()
        # Section header pattern: digit + space + word + / + सू.
        if re.match(r"^[०-९\d]+\s+\S+.*?/\s*सू\..*$", s):
            continue
        # Bracketed editorial notes
        if s.startswith("[") and s.endswith("]"):
            continue
        lines.append(line)
    return "\n".join(lines)


def strip_non_devanagari_lines(text: str) -> str:
    """Remove lines with significant Latin characters (English/IAST leftovers)."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        latin_count = sum(1 for c in stripped if "A" <= c <= "z")
        total = max(len(stripped), 1)
        if latin_count / total > 0.4:
            continue
        lines.append(line)
    return "\n".join(lines)


def split_prose(text: str) -> List[str]:
    """
    Split bhashya prose on । and group 3–4 sentences per chunk.
    Keeps verses (with ॥) intact.
    """
    # Split on ।  or ॥
    parts = re.split(r"([।॥])", text)
    sentences = []
    buf = ""
    for p in parts:
        if p in ("।", "॥"):
            buf += p
            if buf.strip():
                sentences.append(buf.strip())
            buf = ""
        else:
            buf += p
    if buf.strip():
        sentences.append(buf.strip())

    chunks = []
    current = []
    current_len = 0
    GROUP = 3  # sentences per chunk

    for s in sentences:
        if not s or len(s) < 5:
            continue
        current.append(s)
        current_len += len(s)
        if len(current) >= GROUP or current_len >= MAX_CHARS:
            chunk = " ".join(current)
            if len(chunk) >= MIN_CHARS:
                chunks.append(chunk)
            current = []
            current_len = 0

    if current:
        chunk = " ".join(current)
        if len(chunk) >= MIN_CHARS:
            chunks.append(chunk)

    return chunks


def is_garbage_chunk(chunk: str) -> bool:
    """Reject chunks that are mostly ASCII (unconverted English/header lines)."""
    latin = sum(1 for c in chunk if "A" <= c <= "z")
    if latin > 8 and latin / max(len(chunk), 1) > 0.3:
        return True
    # Too many backslashes
    if chunk.count("\\") > 3:
        return True
    return False


def chunk_text(text: str, meta: dict) -> List[dict]:
    text = clean_itrans_artifacts(text)
    text = clean_gretil_artifacts(text)
    text = strip_non_devanagari_lines(text)

    raw_chunks = split_prose(text)

    chunks = []
    for i, raw in enumerate(raw_chunks, start=1):
        if is_garbage_chunk(raw):
            continue
        chunks.append({
            "chunk_id": f"{meta['text_name']}_{i:04d}",
            "text_name": meta["text_name"],
            "text_title_devanagari": meta["title_devanagari"],
            "category": meta["category"],
            "authenticity": meta["authenticity"],
            "source": meta["source"],
            "language": "sa",
            "content": raw,
            "verse_number": str(i),
            "char_count": len(raw),
        })

    return chunks


def load_gita_bhashya() -> str:
    path = CLEAN_DIR / "gitabhashya.txt"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path} — run converter.py first")
    return path.read_text(encoding="utf-8")


def load_bsb() -> str:
    """Merge all 4 adhyaya files into one text."""
    combined = []
    for i in range(1, 5):
        path = CLEAN_DIR / f"brahmasutra_bhashya_adhyaya{i}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Missing: {path} — run gretil_iast_converter.py first")
        combined.append(path.read_text(encoding="utf-8"))
    return "\n\n".join(combined)


def main():
    setup_logging()
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    # Gita Bhashya
    print("=== Gita Bhashya ===")
    gita_text = load_gita_bhashya()
    gita_meta = BHASHYA_META["gitabhashya"]
    gita_chunks = chunk_text(gita_text, gita_meta)
    out = CHUNKS_DIR / "gitabhashya_chunks.json"
    out.write_text(json.dumps(gita_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info(f"gitabhashya: {len(gita_chunks)} chunks → {out}")
    print(f"  {len(gita_chunks)} chunks")
    print("  Sample chunk 1:", gita_chunks[0]["content"][:150] if gita_chunks else "EMPTY")
    print("  Sample chunk 5:", gita_chunks[4]["content"][:150] if len(gita_chunks) > 4 else "")

    # Brahma Sutra Bhashya
    print("\n=== Brahma Sutra Bhashya ===")
    bsb_text = load_bsb()
    bsb_meta = BHASHYA_META["brahmasutra_bhashya"]
    bsb_chunks = chunk_text(bsb_text, bsb_meta)
    out = CHUNKS_DIR / "brahmasutra_bhashya_chunks.json"
    out.write_text(json.dumps(bsb_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info(f"brahmasutra_bhashya: {len(bsb_chunks)} chunks → {out}")
    print(f"  {len(bsb_chunks)} chunks")
    print("  Sample chunk 1:", bsb_chunks[0]["content"][:150] if bsb_chunks else "EMPTY")
    print("  Sample chunk 5:", bsb_chunks[4]["content"][:150] if len(bsb_chunks) > 4 else "")

    print("\n=== bhashya_chunker done ===")


if __name__ == "__main__":
    main()
