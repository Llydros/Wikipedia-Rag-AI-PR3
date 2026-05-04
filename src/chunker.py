"""
Document chunking.

We split text into overlapping windows of CHUNK_SIZE characters. Overlap
prevents a sentence from being split awkwardly across chunks, which would
otherwise hurt retrieval — the embedded vector for a half-sentence is
much weaker than the vector for the same sentence kept whole.

We also try to break on paragraph or sentence boundaries when one is close
to the target cutoff, so chunks read naturally.
"""
from pathlib import Path

from src.config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP


# Look back this many characters from the target end to find a clean break.
BOUNDARY_LOOKBACK = 80


def _find_break(text: str, target_end: int) -> int:
    """
    Try to find a paragraph or sentence boundary just before `target_end`.
    Falls back to `target_end` if nothing nice is nearby.
    """
    if target_end >= len(text):
        return len(text)

    window_start = max(0, target_end - BOUNDARY_LOOKBACK)
    window = text[window_start:target_end]

    # Prefer a paragraph break.
    para = window.rfind("\n\n")
    if para != -1:
        return window_start + para + 2

    # Otherwise a sentence end.
    for punct in (". ", "! ", "? ", ".\n", "!\n", "?\n"):
        idx = window.rfind(punct)
        if idx != -1:
            return window_start + idx + len(punct)

    # Nothing nice — hard cut.
    return target_end


def chunk_text(text: str) -> list[str]:
    """
    Split `text` into overlapping chunks. Returns a list of strings.
    """
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    n = len(text)

    while start < n:
        target_end = min(start + CHUNK_SIZE, n)
        end = _find_break(text, target_end)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        # Slide window forward, leaving CHUNK_OVERLAP characters of overlap.
        start = max(end - CHUNK_OVERLAP, start + 1)

    return chunks


def parse_header(raw: str) -> tuple[str, str, str]:
    """
    Read the small header that ingest.py wrote at the top of each file.
    Expected format:
        # Resolved Title
        # type: person
        <blank line>
        <body...>

    Returns (title, etype, body).
    """
    lines = raw.split("\n", 3)
    if len(lines) < 3 or not lines[0].startswith("# "):
        # No header — treat the whole text as body, with unknown metadata.
        return ("Unknown", "unknown", raw)

    title = lines[0][2:].strip()
    etype_line = lines[1].strip()
    etype = etype_line.replace("# type:", "").strip() if "type:" in etype_line else "unknown"
    body = lines[3] if len(lines) >= 4 else ""
    return (title, etype, body)


def load_and_chunk_all() -> list[dict]:
    """
    Walk DATA_DIR, chunk every .txt file, and return a list of records:
        { "id": str, "text": str, "title": str, "type": str, "source_file": str }

    `id` is unique per chunk and stable across reruns (filename + index).
    """
    records: list[dict] = []
    for txt_file in sorted(DATA_DIR.rglob("*.txt")):
        raw = txt_file.read_text(encoding="utf-8")
        title, etype, body = parse_header(raw)
        chunks = chunk_text(body)
        for i, chunk in enumerate(chunks):
            records.append({
                "id": f"{txt_file.stem}__{i:04d}",
                "text": chunk,
                "title": title,
                "type": etype,
                "source_file": str(txt_file.relative_to(DATA_DIR)),
            })
    return records


if __name__ == "__main__":
    records = load_and_chunk_all()
    print(f"Total chunks: {len(records)}")
    if records:
        print(f"Avg chunk length: {sum(len(r['text']) for r in records) / len(records):.0f} chars")
        # Quick distribution check.
        by_type: dict[str, int] = {}
        for r in records:
            by_type[r["type"]] = by_type.get(r["type"], 0) + 1
        print(f"By type: {by_type}")
        print(f"\nExample chunk (id={records[0]['id']}):")
        print("-" * 60)
        print(records[0]["text"][:300] + "...")