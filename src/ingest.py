"""
Wikipedia ingestion.
For each entity in config.ENTITIES, fetch the article and save the plain
text to data/{type}/{slug}.txt. Skips entities that are already on disk
so reruns are cheap.
"""
import re
import sys
from pathlib import Path

import wikipediaapi

from src.config import ENTITIES, DATA_DIR


# Wikipedia's API requires a contact / project identifier in the User-Agent.
# Replace the email if you want; it just needs to be non-empty.
USER_AGENT = "WikipediaRAG/1.0 (educational project; contact: student@example.com)"


def slugify(title: str) -> str:
    """Convert a Wikipedia title into a safe filename."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)   # non-alphanumeric -> underscore
    slug = slug.strip("_")
    return slug


def ensure_dirs() -> None:
    (DATA_DIR / "person").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "place").mkdir(parents=True, exist_ok=True)


def fetch_one(wiki: wikipediaapi.Wikipedia, entity: dict) -> tuple[str, str] | None:
    """
    Fetch a single Wikipedia article. Returns (text, resolved_title) or None
    if the page does not exist.
    """
    page = wiki.page(entity["title"])
    if not page.exists():
        return None
    # `page.text` returns the full plain-text article (no markup).
    return page.text, page.title


def ingest_all(force: bool = False) -> None:
    """
    Fetch every entity in config.ENTITIES.
    If `force` is False, skip entities whose file already exists.
    """
    ensure_dirs()
    wiki = wikipediaapi.Wikipedia(user_agent=USER_AGENT, language="en")

    success, skipped, failed = 0, 0, 0

    for entity in ENTITIES:
        title = entity["title"]
        etype = entity["type"]
        slug = slugify(title)
        out_path = DATA_DIR / etype / f"{slug}.txt"

        if out_path.exists() and not force:
            print(f"[skip] {title}  (already on disk)")
            skipped += 1
            continue

        print(f"[fetch] {title} ...", end=" ", flush=True)
        result = fetch_one(wiki, entity)
        if result is None:
            print("NOT FOUND")
            failed += 1
            continue

        text, resolved_title = result
        # Prepend a small header so the chunker / retriever knows the source.
        header = f"# {resolved_title}\n# type: {etype}\n\n"
        out_path.write_text(header + text, encoding="utf-8")
        print(f"ok ({len(text):,} chars)")
        success += 1

    print()
    print(f"Done. fetched={success}  skipped={skipped}  failed={failed}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    ingest_all(force=force)