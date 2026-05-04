"""
Query routing + retrieval.

Two-stage process:

  1. ROUTING — figure out whether the query is about a person, a place,
     or both. We do this with simple keyword matching against the entity
     titles in config.ENTITIES, plus a small list of topic words (e.g.
     "discovered", "born" -> person; "located", "tourist" -> place).
     The PDF explicitly allows rule-based routing.

  2. RETRIEVAL — embed the query with the same model used at index time
     and run a similarity search against ChromaDB. If routing decided
     "person" or "place" (but not both), we apply a metadata filter so
     we only score against the relevant subset.
"""
import re

import ollama

from src.config import ENTITIES, EMBED_MODEL, TOP_K
from src.embed_store import get_collection


# Keyword hints that bias routing toward one type when no entity name matches.
PERSON_HINTS = {
    "who", "person", "people", "scientist", "artist", "writer",
    "musician", "singer", "athlete", "footballer", "physicist",
    "born", "died", "discovered", "invented", "wrote", "painted",
    "composed", "played", "winning", "won", "his", "her",
}

PLACE_HINTS = {
    "where", "place", "city", "country", "located", "location",
    "monument", "building", "tower", "wall", "mountain", "river",
    "tomb", "temple", "palace", "ruins", "tourist", "visit",
    "stands", "situated",
}


# Pre-compute lowercased entity names for matching.
_PEOPLE_LOWER = [e["title"].lower() for e in ENTITIES if e["type"] == "person"]
_PLACES_LOWER = [e["title"].lower() for e in ENTITIES if e["type"] == "place"]


def _tokens(text: str) -> set[str]:
    """Lowercase word tokens for keyword matching."""
    return set(re.findall(r"[a-z]+", text.lower()))


def _mentions(query_lower: str, entity_names: list[str]) -> list[str]:
    """
    Return entity names that appear in the query as substrings.
    Substring matching is intentional — it handles "Einstein" matching
    "Albert Einstein" and "Eiffel" matching "Eiffel Tower".
    """
    hits = []
    for name in entity_names:
        # Match by full name or by the most distinctive token (last word).
        last_token = name.split()[-1]
        if name in query_lower:
            hits.append(name)
        elif len(last_token) >= 4 and re.search(rf"\b{re.escape(last_token)}\b", query_lower):
            hits.append(name)
    return hits


def route_query(query: str) -> str:
    """
    Return one of: "person", "place", "both".

    Decision rules, in order:
      1. If the query mentions both a known person AND a known place -> "both".
      2. If it mentions only a person -> "person". Only a place -> "place".
      3. Otherwise fall back to topic keywords (PERSON_HINTS / PLACE_HINTS).
      4. If still ambiguous, default to "both" (let retrieval decide).
    """
    q = query.lower()

    has_person = bool(_mentions(q, _PEOPLE_LOWER))
    has_place = bool(_mentions(q, _PLACES_LOWER))

    if has_person and has_place:
        return "both"
    if has_person:
        return "person"
    if has_place:
        return "place"

    # No entity name found — try topic words.
    toks = _tokens(query)
    person_score = len(toks & PERSON_HINTS)
    place_score = len(toks & PLACE_HINTS)

    if person_score > place_score:
        return "person"
    if place_score > person_score:
        return "place"

    return "both"


def embed_query(query: str) -> list[float]:
    """Embed the query with the same model used for chunks."""
    resp = ollama.embeddings(model=EMBED_MODEL, prompt=query)
    return resp["embedding"]


def retrieve(query: str, top_k: int = TOP_K) -> dict:
    """
    Full retrieval pipeline. Returns:
      {
        "route": "person" | "place" | "both",
        "chunks": [
            {"text": ..., "title": ..., "type": ..., "score": ..., "id": ...},
            ...
        ]
      }
    `score` is a similarity in [0, 1] derived from Chroma's cosine distance.
    """
    route = route_query(query)
    qvec = embed_query(query)

    where = None
    if route in ("person", "place"):
        where = {"type": route}

    collection = get_collection(reset=False)
    raw = collection.query(
        query_embeddings=[qvec],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    dists = raw["distances"][0]
    ids = raw["ids"][0]

    for doc, meta, dist, cid in zip(docs, metas, dists, ids):
        chunks.append({
            "id": cid,
            "text": doc,
            "title": meta.get("title", "Unknown"),
            "type": meta.get("type", "unknown"),
            # Chroma returns cosine *distance* in [0,2]; convert to similarity.
            "score": max(0.0, 1.0 - dist / 2.0),
        })

    return {"route": route, "chunks": chunks}


# --- Manual test block ---
if __name__ == "__main__":
    test_queries = [
        "Who was Albert Einstein and what is he known for?",
        "Where is Mount Everest?",
        "Compare the Eiffel Tower and the Statue of Liberty",
        "Which famous place is located in Turkey?",
        "Who is the president of Mars?",
    ]
    for q in test_queries:
        result = retrieve(q, top_k=3)
        print(f"\nQ: {q}")
        print(f"  route: {result['route']}")
        for i, ch in enumerate(result["chunks"], 1):
            print(f"  [{i}] {ch['title']:<25}  type={ch['type']:<6}  score={ch['score']:.3f}")
            preview = ch["text"][:80].replace("\n", " ")
            print(f"      {preview}...")