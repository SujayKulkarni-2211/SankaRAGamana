"""
Fetches Advaita Vedanta plain text files from GRETIL.
Parses the GRETIL index page for Shankara-related files.
Saves to corpus/raw/gretil/
"""

import os
import time
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

GRETIL_BASE = "https://gretil.sub.uni-goettingen.de/gretil/"
GRETIL_ADVAITA_INDEX = "https://gretil.sub.uni-goettingen.de/gretil.htm"
RAW_DIR = Path("corpus/raw/gretil")
LOG_DIR = Path("logs")

SHANKARA_KEYWORDS = [
    "shankara", "sankara", "shankar", "advaita", "shankaracharya",
    "brahmasutra", "bhashya", "vedanta"
]


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


def fetch_shankara_links() -> list:
    """Parse GRETIL index page for Shankara-related text file links."""
    try:
        resp = requests.get(GRETIL_ADVAITA_INDEX, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch GRETIL index: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True).lower()
        if any(kw in text or kw in href.lower() for kw in SHANKARA_KEYWORDS):
            if href.endswith((".txt", ".htm", ".html")):
                full_url = urljoin(GRETIL_BASE, href)
                links.append({"url": full_url, "link_text": a.get_text(strip=True)})

    logging.info(f"Found {len(links)} potential Shankara links on GRETIL index")
    return links


def download_file(url: str, link_text: str) -> bool:
    filename = url.split("/")[-1]
    dest = RAW_DIR / filename
    meta_dest = RAW_DIR / f"{filename}_meta.json"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        meta_dest.write_text(
            json.dumps(
                {
                    "filename": filename,
                    "source_url": url,
                    "link_text": link_text,
                    "source": "gretil",
                    "downloaded_at": datetime.utcnow().isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        logging.info(f"OK  {filename}")
        return True
    except Exception as e:
        logging.error(f"FAIL {url}: {e}")
        return False


def main():
    setup_logging()
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    links = fetch_shankara_links()
    if not links:
        print("No links found — check GRETIL index URL or keywords.")
        return

    success, failed = 0, 0
    for item in links:
        if download_file(item["url"], item["link_text"]):
            success += 1
        else:
            failed += 1
        time.sleep(1)

    print(f"\n=== gretil_fetcher done: {success} downloaded, {failed} failed ===")


if __name__ == "__main__":
    main()
