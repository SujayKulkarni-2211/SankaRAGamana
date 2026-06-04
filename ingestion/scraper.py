"""
Downloads all .itx files from sanskritdocuments.org
Saves to corpus/raw/itrans/
Logs success/failure to logs/ingestion.log
Does NOT process anything — only downloads
"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

BASE_URL = "https://sanskritdocuments.org/all_itrans/{filename}"
RAW_DIR = Path("corpus/raw/itrans")
LOG_DIR = Path("logs")

SHANKARA_ITX_FILES = [
    # (text_name, filename, category, authenticity)
    ("tattvabodha", "tattvabodha.itx", "prakarana", "confirmed"),
    ("vivekachudamani", "viveknew.itx", "prakarana", "attributed"),
    ("atmabodha", "atmabodha.itx", "prakarana", "attributed"),
    ("upadeshasahasri", "upadeshasaahasrii1.itx", "prakarana", "confirmed"),
    ("aparokshanubhuti", "aparokshaanubhuuti.itx", "prakarana", "attributed"),
    ("panchikaran", "paJNchi.itx", "prakarana", "attributed"),
    ("vakyavritti", "vaakyavritti.itx", "prakarana", "attributed"),
    ("manishapanchakam", "manisha5.itx", "prakarana", "attributed"),
    ("sadhanapanchakam", "sadhana5.itx", "prakarana", "attributed"),
    ("mayapanchakam", "mAyA5.itx", "prakarana", "attributed"),
    ("prashnottararatnamalika", "prashnottara.itx", "prakarana", "attributed"),
    ("soundaryalahari", "soundaryalahari.itx", "stotra", "attributed"),
    ("anandalahari", "anandalahari.itx", "stotra", "attributed"),
    ("dakshinamurti_stotram", "dakshinamurti.itx", "stotra", "attributed"),
    ("nirvanashatakam", "nirvana6.itx", "stotra", "attributed"),
    ("bhajagovindam", "bhajagovindam.itx", "stotra", "attributed"),
    ("guruashtakam", "gurvashtakam.itx", "stotra", "attributed"),
    ("kalabhairava_ashtakam", "kaalabhairava8.itx", "stotra", "attributed"),
    ("ganesha_pancharatnam", "ganesha5.itx", "stotra", "attributed"),
    ("sivapanchakshara", "shivapanchakshara.itx", "stotra", "attributed"),
]


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "ingestion.log"),
            logging.StreamHandler(),
        ],
    )


def download_file(text_name: str, filename: str, category: str, authenticity: str) -> bool:
    url = BASE_URL.format(filename=filename)
    dest = RAW_DIR / filename
    meta_dest = RAW_DIR / f"{text_name}_meta.json"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        dest.write_bytes(response.content)
        meta_dest.write_text(
            json.dumps(
                {
                    "text_name": text_name,
                    "filename": filename,
                    "source_url": url,
                    "category": category,
                    "authenticity": authenticity,
                    "downloaded_at": datetime.utcnow().isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        logging.info(f"OK  {text_name} → {dest}")
        return True
    except Exception as e:
        logging.error(f"FAIL {text_name} ({url}): {e}")
        return False


def main():
    setup_logging()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    success, failed = 0, 0
    for text_name, filename, category, authenticity in SHANKARA_ITX_FILES:
        if download_file(text_name, filename, category, authenticity):
            success += 1
        else:
            failed += 1
        time.sleep(1)  # polite delay

    print(f"\n=== scraper done: {success} downloaded, {failed} failed ===")


if __name__ == "__main__":
    main()
