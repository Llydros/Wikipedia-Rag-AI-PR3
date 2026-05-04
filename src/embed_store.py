"""
Embedding + vector storage.

Pipeline:
  1. Load chunks (via chunker.load_and_chunk_all).
  2. Send each chunk's text to Ollama's embedding endpoint
     (model: nomic-embed-text). We batch in groups so the call overhead
     amortizes nicely.
  3. Store (id, embedding, text, metadata) in a Chroma persistent collection.

We use ONE collection with a `type` metadata field (Option B in the brief).
At query time we either filter by type or skip the filter for mixed queries.
"""
import sys
import time

import chromadb
import ollama

from src.chunker import load_and_chunk_all
from src.config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL


# How many chunks to send to Ollama per round-trip. Ollama embeds one at a
# time internally, so this just controls our progress reporting + retries.
BATCH_SIZE = 32


def get_collection(reset: bool = False) -> chromadb.Collection:
    """
    Open (or create) the persistent Chroma collection.
    If `reset` is True, drop and recreate the collection — useful when
    chunking strategy or entity list changes.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[reset] deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass  # didn't exist; that's fine

    # We pass embedding_function=None because we compute embeddings ourselves
    # (via Ollama) and pass them in directly. Letting Chroma do it would
    # require a Chroma-native embedder.
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for text
    )
    return collection


def embed_one(text: str) -> list[float]:
    """Call Ollama for a single embedding. Used as the per-item primitive."""
    resp = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return resp["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts. Ollama's Python client doesn't expose a true
    batch endpoint for embeddings, so we loop. We keep this in one place
    so we can swap in a batched backend later without touching callers.
    """
    return [embed_one(t) for t in texts]


def build_index(reset: bool = True) -> None:
    """
    Full rebuild: load chunks, embed them, write to Chroma.
    Default `reset=True` because re-embedding with a stale collection
    underneath leads to confusing duplication.
    """
    print("Loading chunks ...")
    records = load_and_chunk_all()
    if not records:
        print("No chunks found. Did you run `python -m src.ingest` first?")
        sys.exit(1)
    print(f"  {len(records):,} chunks ready.\n")

    collection = get_collection(reset=reset)

    print(f"Embedding with '{EMBED_MODEL}' (batch={BATCH_SIZE}) ...")
    t0 = time.time()
    total = len(records)

    for start in range(0, total, BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]
        texts = [r["text"] for r in batch]
        ids = [r["id"] for r in batch]
        metadatas = [
            {"title": r["title"], "type": r["type"], "source_file": r["source_file"]}
            for r in batch
        ]

        try:
            vectors = embed_batch(texts)
        except Exception as e:
            print(f"\n[error] batch starting at {start} failed: {e}")
            print("  retrying once after 2s ...")
            time.sleep(2)
            vectors = embed_batch(texts)  # one retry; let it raise if it fails again

        collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas,
        )

        # Progress line: overwrite the same row.
        done = start + len(batch)
        pct = done / total * 100
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(
            f"\r  {done:>5}/{total}  ({pct:5.1f}%)  "
            f"{rate:5.1f} chunks/s  eta {eta:5.0f}s",
            end="",
            flush=True,
        )

    print(f"\n\nDone. Indexed {total:,} chunks in {time.time() - t0:.1f}s.")
    print(f"Collection size: {collection.count():,}")


if __name__ == "__main__":
    reset = "--no-reset" not in sys.argv
    build_index(reset=reset)