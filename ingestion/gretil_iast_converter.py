"""
Converts GRETIL IAST-encoded .htm files to Unicode Devanagari .txt files.
Strips HTML tags, removes the character-map header, converts IAST → Devanagari.
Saves to corpus/clean/devanagari/
"""

import re
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

GRETIL_DIR = Path("corpus/raw/gretil")
CLEAN_DIR  = Path("corpus/clean/devanagari")
LOG_DIR    = Path("logs")

# Map GRETIL filename stem → (text_name, title_devanagari, meta)
GRETIL_FILES = {
    "brssbh1u": {
        "text_name": "brahmasutra_bhashya",
        "title": "ब्रह्मसूत्रशाङ्करभाष्यम्",
        "adhyaya": 1,
    },
    "brssbh2u": {
        "text_name": "brahmasutra_bhashya",
        "title": "ब्रह्मसूत्रशाङ्करभाष्यम्",
        "adhyaya": 2,
    },
    "brssbh3u": {
        "text_name": "brahmasutra_bhashya",
        "title": "ब्रह्मसूत्रशाङ्करभाष्यम्",
        "adhyaya": 3,
    },
    "brssbh4u": {
        "text_name": "brahmasutra_bhashya",
        "title": "ब्रह्मसूत्रशाङ्करभाष्यम्",
        "adhyaya": 4,
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


def strip_gretil_header(text: str) -> str:
    """Remove the character-map header that GRETIL prepends to every file."""
    # Header ends at 'Unless indic' or the first substantive Sanskrit line
    # Find the last occurrence of the character table pattern
    marker = "Unless indic"
    idx = text.find(marker)
    if idx != -1:
        text = text[idx + len(marker):]
        # Skip to next newline
        nl = text.find("\n")
        if nl != -1:
            text = text[nl:]
    return text


def clean_reference_tags(text: str) -> str:
    """Remove GRETIL reference tags like |BBs_1,1.1| and /BBs_..../"""
    text = re.sub(r"\|[A-Z][A-Za-z_0-9,\.]+\|", "", text)
    text = re.sub(r"/[A-Z][A-Za-z_0-9,\.]+/", "", text)
    return text


def strip_ascii_lines(text: str) -> str:
    """Remove lines that are purely ASCII (section headers, English notes)."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        # Keep line if it contains any non-ASCII character (IAST diacritics)
        if any(ord(c) > 127 for c in stripped):
            lines.append(line)
        # Keep short lines that might be verse/sutra markers with diacritics
    return "\n".join(lines)


def convert_file(htm_path: Path, out_path: Path) -> bool:
    try:
        raw = htm_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        text = soup.get_text(separator="\n")

        text = strip_gretil_header(text)
        text = clean_reference_tags(text)
        text = strip_ascii_lines(text)

        # Convert IAST → Devanagari
        devanagari = transliterate(text, sanscript.IAST, sanscript.DEVANAGARI)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(devanagari, encoding="utf-8")
        logging.info(f"Converted {htm_path.name} → {out_path.name}")
        return True
    except Exception as e:
        logging.error(f"FAIL convert {htm_path.name}: {e}")
        import traceback; traceback.print_exc()
        return False


def main():
    setup_logging()
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    success, failed = 0, 0
    for stem, meta in GRETIL_FILES.items():
        htm_path = GRETIL_DIR / f"{stem}.htm"
        if not htm_path.exists():
            logging.warning(f"Missing: {htm_path}")
            failed += 1
            continue
        out_name = f"{meta['text_name']}_adhyaya{meta['adhyaya']}.txt"
        out_path = CLEAN_DIR / out_name
        if convert_file(htm_path, out_path):
            success += 1
            # Show sample
            sample = out_path.read_text(encoding="utf-8")
            non_empty = [l for l in sample.splitlines() if l.strip()][:3]
            print(f"\n[{out_name}] first 3 non-empty lines:")
            for l in non_empty:
                print(f"  {l[:120]}")
        else:
            failed += 1

    print(f"\n=== gretil_iast_converter done: {success} converted, {failed} failed ===")


if __name__ == "__main__":
    main()
