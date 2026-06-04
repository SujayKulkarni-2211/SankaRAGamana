"""
Converts ITRANS-encoded .itx files to Unicode Devanagari.
Saves to corpus/clean/devanagari/
Strips metadata lines (% prefix) and LaTeX commands (\ prefix).
"""

import re
import logging
from pathlib import Path

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

RAW_DIR = Path("corpus/raw/itrans")
CLEAN_DIR = Path("corpus/clean/devanagari")
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


def strip_metadata(text: str) -> str:
    """Remove % metadata lines, LaTeX \\commands, #directives, and ##SECTION## markers."""
    import re
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("%") or stripped.startswith("\\") or stripped.startswith("#"):
            continue
        # Strip inline ##SECTION LABEL## markers (often English inside Sanskrit files)
        line = re.sub(r"##[^#]*##", "", line)
        lines.append(line)
    return "\n".join(lines)


def convert_file(itx_path: Path, out_path: Path) -> bool:
    try:
        raw = itx_path.read_text(encoding="utf-8", errors="replace")
        cleaned = strip_metadata(raw)
        devanagari = transliterate(cleaned, sanscript.ITRANS, sanscript.DEVANAGARI)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(devanagari, encoding="utf-8")
        logging.info(f"Converted {itx_path.name} → {out_path.name}")
        return True
    except Exception as e:
        logging.error(f"FAIL convert {itx_path.name}: {e}")
        return False


def main():
    setup_logging()
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    itx_files = list(RAW_DIR.glob("*.itx"))
    if not itx_files:
        print(f"No .itx files found in {RAW_DIR}")
        return

    success, failed = 0, 0
    for itx_path in itx_files:
        out_path = CLEAN_DIR / itx_path.with_suffix(".txt").name
        if convert_file(itx_path, out_path):
            success += 1
        else:
            failed += 1

    print(f"\n=== converter done: {success} converted, {failed} failed ===")

    # Print 3 sample chunks to verify Devanagari
    print("\n--- Sample output (first 3 converted files, first 200 chars each) ---")
    for path in list(CLEAN_DIR.glob("*.txt"))[:3]:
        print(f"\n[{path.name}]")
        print(path.read_text(encoding="utf-8")[:200])


if __name__ == "__main__":
    main()
