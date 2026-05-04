"""
One-command index builder.

Usage:
    python build_index.py              # incremental: skip already-fetched articles
    python build_index.py --force      # re-fetch every Wikipedia article
    python build_index.py --no-reset   # keep existing Chroma vectors (advanced)

Default behavior:
    1. Ingest any missing Wikipedia articles into data/.
    2. Wipe the Chroma collection and re-embed every chunk.

The wipe-on-rebuild is intentional: chunking strategy or entity list
changes invalidate old vectors silently if we don't reset.
"""
import sys
import time

from src.ingest import ingest_all
from src.embed_store import build_index


def main() -> None:
    force_fetch = "--force" in sys.argv
    keep_vectors = "--no-reset" in sys.argv

    print("=" * 60)
    print("STEP 1/2 — Ingesting Wikipedia articles")
    print("=" * 60)
    t0 = time.time()
    ingest_all(force=force_fetch)
    print(f"Ingest finished in {time.time() - t0:.1f}s\n")

    print("=" * 60)
    print("STEP 2/2 — Embedding + indexing chunks")
    print("=" * 60)
    t1 = time.time()
    build_index(reset=not keep_vectors)
    print(f"Index build finished in {time.time() - t1:.1f}s\n")

    print("All done. You can now run:")
    print("    streamlit run app.py")


if __name__ == "__main__":
    main()