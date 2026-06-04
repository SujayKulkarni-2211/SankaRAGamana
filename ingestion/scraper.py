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

BASE = "https://sanskritdocuments.org"
RAW_DIR = Path("corpus/raw/itrans")
LOG_DIR = Path("logs")

SHANKARA_ITX_FILES = [
    # (text_name, url_path, category, authenticity)
    # --- Prakarana Granthas ---
    ("tattvabodha",           "/doc_z_misc_major_works/tattvabodha.itx",          "prakarana", "confirmed"),
    ("vivekachudamani",       "/doc_z_misc_shankara/viveknew.itx",                "prakarana", "attributed"),
    ("atmabodha",             "/doc_z_misc_shankara/aatmabodha.itx",              "prakarana", "attributed"),
    ("upadeshasahasri",       "/doc_z_misc_shankara/upadeshasaahasrii1.itx",      "prakarana", "confirmed"),
    ("aparokshanubhuti",      "/doc_z_misc_shankara/aparokshaanubhuuti.itx",      "prakarana", "attributed"),
    ("panchikaran",           "/doc_z_misc_shankara/paJNchi.itx",                 "prakarana", "attributed"),
    ("vakyavritti",           "/doc_z_misc_shankara/vaakyavritti.itx",            "prakarana", "attributed"),
    ("manishapanchakam",      "/doc_z_misc_shankara/manishhaa5.itx",              "prakarana", "attributed"),
    ("sadhanapanchakam",      "/doc_z_misc_shankara/saadhana-panchakam.itx",      "prakarana", "attributed"),
    ("mayapanchakam",         "/doc_z_misc_shankara/mAyA5.itx",                   "prakarana", "attributed"),
    ("prashnottararatnamalika", "/doc_z_misc_shankara/prashnottara.itx",          "prakarana", "attributed"),
    ("laghuvakhyavritti",     "/doc_z_misc_shankara/laghuvak.itx",                "prakarana", "attributed"),
    ("ekashloki",             "/doc_z_misc_shankara/ekashloki.itx",               "prakarana", "attributed"),
    ("dashashloki",           "/doc_z_misc_shankara/dashashl.itx",                "prakarana", "attributed"),
    ("tattvopadesha",         "/doc_z_misc_shankara/tattvopadesha.itx",           "prakarana", "attributed"),
    ("drigdrishyaviveka",     "/doc_z_misc_major_works/drigdrishyaviveka.itx",    "prakarana", "attributed"),
    ("brahmajna",             "/doc_z_misc_shankara/brahmajna.itx",               "prakarana", "attributed"),
    ("advaitanubhuti",        "/doc_z_misc_shankara/advaitanubhuti.itx",          "prakarana", "attributed"),
    # --- Stotras ---
    ("bhajagovindam",         "/doc_vishhnu/bhajagovindam.itx",                   "stotra",    "attributed"),
    ("dakshinamurti_stotram", "/doc_shiva/dakshina.itx",                          "stotra",    "attributed"),
    ("kalabhairava_ashtakam", "/doc_shiva/kaalabhairava.itx",                     "stotra",    "attributed"),
    ("ganesha_pancharatnam",  "/doc_ganesha/ganesha5.itx",                        "stotra",    "attributed"),
    ("guruashtakam",          "/doc_deities_misc/gurvashtakam.itx",               "stotra",    "attributed"),
    ("kashipanchakam",        "/doc_z_misc_shankara/kashipanchakam.itx",          "stotra",    "attributed"),
    ("kaupinapanchakam",      "/doc_z_misc_shankara/kaupiina5.itx",               "stotra",    "attributed"),
    ("yatipanchakam",         "/doc_z_misc_shankara/yati5.itx",                   "stotra",    "attributed"),
    ("totakashtakam",         "/doc_z_misc_shankara/totaka8.itx",                 "stotra",    "attributed"),
    ("svarupa_ashtakam",      "/doc_z_misc_shankara/svarupa-8.itx",               "stotra",    "attributed"),
    # --- Bhashyas (Upanishad commentaries) ---
    ("isha_bhashya",          "/doc_upanishhat/IshAvAsyopanishadshAnkarabhAShya.itx", "bhashya", "confirmed"),
    ("kena_bhashya",          "/doc_upanishhat/kenopaniShadshAnkarabhAShya.itx",  "bhashya",   "confirmed"),
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


def download_file(text_name: str, url_path: str, category: str, authenticity: str) -> bool:
    url = BASE + url_path
    filename = url_path.split("/")[-1]
    dest = RAW_DIR / filename
    meta_dest = RAW_DIR / f"{text_name}_meta.json"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
        response = requests.get(url, timeout=30, headers=headers)
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
    for text_name, url_path, category, authenticity in SHANKARA_ITX_FILES:
        if download_file(text_name, url_path, category, authenticity):
            success += 1
        else:
            failed += 1
        time.sleep(1)  # polite delay

    print(f"\n=== scraper done: {success} downloaded, {failed} failed ===")


if __name__ == "__main__":
    main()
