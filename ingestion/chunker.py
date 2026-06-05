"""
Splits converted Devanagari text into chunks on verse boundaries.
Primary split: ॥ (double daṇḍa)
Bhāṣya prose (no ॥): split on । and group 3-5 sentences
Saves per-text JSON to corpus/chunks/{text_name}_chunks.json
"""

import json
import re
import logging
from pathlib import Path
from typing import List

CLEAN_DIR = Path("corpus/clean/devanagari")
CHUNKS_DIR = Path("corpus/chunks")
LOG_DIR = Path("logs")

MIN_CHARS = 20
MAX_CHARS = 500

# Devanagari title lookup
TITLE_MAP = {
    "tattvabodha": "तत्त्वबोधः",
    "viveknew": "विवेकचूडामणिः",
    "atmabodha": "आत्मबोधः",
    "upadeshasaahasrii1": "उपदेशसाहस्री",
    "aparokshaanubhuuti": "अपरोक्षानुभूतिः",
    "paJNchi": "पञ्चीकरणम्",
    "vaakyavritti": "वाक्यवृत्तिः",
    "manisha5": "मनीषापञ्चकम्",
    "sadhana5": "साधनपञ्चकम्",
    "mAyA5": "मायापञ्चकम्",
    "prashnottara": "प्रश्नोत्तररत्नमालिका",
    "soundaryalahari": "सौन्दर्यलहरी",
    "anandalahari": "आनन्दलहरी",
    "dakshinamurti": "दक्षिणामूर्तिस्तोत्रम्",
    "nirvana6": "निर्वाणषट्कम्",
    "bhajagovindam": "भजगोविन्दम्",
    "gurvashtakam": "गुर्वष्टकम्",
    "kaalabhairava8": "कालभैरवाष्टकम्",
    "ganesha5": "गणेशपञ्चरत्नम्",
    "shivapanchakshara": "शिवपञ्चाक्षरस्तोत्रम्",
}

# text_name lookup (filename stem → canonical text_name)
NAME_MAP = {
    "tattvabodha": "tattvabodha",
    "viveknew": "vivekachudamani",
    "atmabodha": "atmabodha",
    "upadeshasaahasrii1": "upadeshasahasri",
    "aparokshaanubhuuti": "aparokshanubhuti",
    "paJNchi": "panchikaran",
    "vaakyavritti": "vakyavritti",
    "manisha5": "manishapanchakam",
    "sadhana5": "sadhanapanchakam",
    "mAyA5": "mayapanchakam",
    "prashnottara": "prashnottararatnamalika",
    "soundaryalahari": "soundaryalahari",
    "anandalahari": "anandalahari",
    "dakshinamurti": "dakshinamurti_stotram",
    "nirvana6": "nirvanashatakam",
    "bhajagovindam": "bhajagovindam",
    "gurvashtakam": "guruashtakam",
    "kaalabhairava8": "kalabhairava_ashtakam",
    "ganesha5": "ganesha_pancharatnam",
    "shivapanchakshara": "sivapanchakshara",
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


def split_by_double_danda(text: str) -> List[str]:
    """Split on ॥, keep verse boundary content."""
    parts = re.split(r"॥", text)
    return [p.strip() for p in parts if len(p.strip()) >= MIN_CHARS]


def split_prose(text: str, group_size: int = 4) -> List[str]:
    """Split bhāṣya prose on । and group sentences."""
    sentences = [s.strip() for s in re.split(r"।", text) if len(s.strip()) >= MIN_CHARS]
    groups = []
    for i in range(0, len(sentences), group_size):
        chunk = "। ".join(sentences[i : i + group_size])
        if chunk:
            groups.append(chunk)
    return groups


# Consonants that take nukta (़) in Sanskrit loanwords/foreign words but NOT in native Sanskrit
# फ़ ज़ क़ ग़ — these indicate transliterated English remaining after conversion
_FOREIGN_NUKTA_RE = re.compile(r"[फजकग]़")
# Kannada Unicode block
_KANNADA_RE = re.compile(r"[ಀ-೿]")
# Roman characters (4+ consecutive) inside a Devanagari chunk = transliterated English
_ROMAN_IN_DEVA_RE = re.compile(r"[a-zA-Z]{4,}")


def is_garbage_line(line: str) -> bool:
    """True if line is transliterated English or contains non-Sanskrit script."""
    if _FOREIGN_NUKTA_RE.search(line):
        return True
    if _KANNADA_RE.search(line):
        return True
    return False


def is_garbage_chunk(chunk: str) -> bool:
    """True if the whole chunk is transliterated English prose (not Sanskrit)."""
    if _ROMAN_IN_DEVA_RE.search(chunk):
        return True
    return False


def strip_garbage_lines(text: str) -> str:
    """Remove lines containing transliterated-English Devanagari before chunking."""
    return "\n".join(
        line for line in text.splitlines()
        if not is_garbage_line(line)
    )


def enforce_max_size(chunk: str) -> List[str]:
    """Split chunk at nearest । if longer than MAX_CHARS."""
    if len(chunk) <= MAX_CHARS:
        return [chunk]
    parts = re.split(r"।", chunk)
    result, current = [], ""
    for part in parts:
        if len(current) + len(part) + 1 > MAX_CHARS and current:
            result.append(current.strip())
            current = part
        else:
            current += ("। " if current else "") + part
    if current.strip():
        result.append(current.strip())
    return result


def chunk_text(text: str, text_name: str, stem: str, category: str, authenticity: str, source: str) -> List[dict]:
    title_devanagari = TITLE_MAP.get(stem, "")
    text = strip_garbage_lines(text)
    has_double_danda = "॥" in text
    raw_chunks = split_by_double_danda(text) if has_double_danda else split_prose(text)

    chunks = []
    verse_counter = 1
    for raw in raw_chunks:
        for part in enforce_max_size(raw):
            if len(part) < MIN_CHARS:
                continue
            if is_garbage_chunk(part):
                continue
            chunk_id = f"{text_name}_{verse_counter:03d}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text_name": text_name,
                    "text_title_devanagari": title_devanagari,
                    "category": category,
                    "authenticity": authenticity,
                    "source": source,
                    "language": "sa",
                    "content": part,
                    "verse_number": str(verse_counter),
                    "char_count": len(part),
                }
            )
            verse_counter += 1

    return chunks


def load_meta(stem: str) -> dict:
    """Load metadata from scraper-generated _meta.json if available."""
    meta_path = Path("corpus/raw/itrans") / f"{stem}_meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text())
    return {"category": "prakarana", "authenticity": "attributed", "source": "sanskritdocuments.org"}


def chunk_file(txt_path: Path) -> List[dict]:
    stem = txt_path.stem
    text_name = NAME_MAP.get(stem, stem)
    meta = load_meta(stem)
    text = txt_path.read_text(encoding="utf-8")
    return chunk_text(
        text,
        text_name=text_name,
        stem=stem,
        category=meta.get("category", "prakarana"),
        authenticity=meta.get("authenticity", "attributed"),
        source=meta.get("source", "sanskritdocuments.org"),
    )


def main():
    setup_logging()
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    txt_files = list(CLEAN_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No converted files found in {CLEAN_DIR}")
        return

    total_chunks = 0
    for txt_path in txt_files:
        stem = txt_path.stem
        text_name = NAME_MAP.get(stem, stem)
        chunks = chunk_file(txt_path)
        out_path = CHUNKS_DIR / f"{text_name}_chunks.json"
        out_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        logging.info(f"{text_name}: {len(chunks)} chunks → {out_path}")
        total_chunks += len(chunks)

    print(f"\n=== chunker done: {len(txt_files)} texts, {total_chunks} total chunks ===")


if __name__ == "__main__":
    main()
