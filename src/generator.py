"""
Answer generation via local LLM (Ollama).

We build a strict, grounded prompt:
  - The system instruction tells the model to use ONLY the provided
    context and to produce a defined refusal phrase if it can't.
  - The user message contains the numbered context chunks followed by
    the question.
  - We also enforce refusal programmatically: if all retrieved chunks
    score below MIN_SCORE_THRESHOLD, OR the model returns an empty
    answer, we override with the canonical refusal phrase.
"""
from collections.abc import Iterator

import ollama

from src.config import LLM_MODEL


REFUSAL = "I don't know based on the provided information."

# If the best retrieved chunk's similarity is below this, we don't even
# call the LLM — the corpus simply doesn't contain the answer. This
# threshold was chosen empirically: relevant queries typically score
# > 0.55, off-topic queries score < 0.45.
MIN_SCORE_THRESHOLD = 0.45


SYSTEM_PROMPT = f"""You are a helpful assistant that answers questions about famous people and famous places using ONLY the provided CONTEXT.

You MUST follow these rules:
1. Use ONLY the information in the CONTEXT. Do not use any outside knowledge.
2. If the CONTEXT does not contain enough information to answer the question, your entire response must be exactly: {REFUSAL}
3. Always produce a response. Never return an empty answer.
4. Be concise and factual. Do not invent dates, names, or numbers.
5. For comparisons, structure the answer with both entities clearly separated.
6. You may cite which entity each fact comes from (e.g. "According to the Albert Einstein article, ...") when useful.
"""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Render retrieved chunks + question into a single user message."""
    if not chunks:
        return (
            "CONTEXT:\n(no relevant context was retrieved)\n\n"
            f"QUESTION: {query}\n\n"
            "Answer:"
        )

    lines = ["CONTEXT:"]
    for i, ch in enumerate(chunks, 1):
        title = ch.get("title", "Unknown")
        etype = ch.get("type", "unknown")
        text = ch.get("text", "").strip()
        lines.append(f"[{i}] ({etype}: {title})\n{text}")
        lines.append("")

    lines.append(f"QUESTION: {query}")
    lines.append("")
    lines.append("Answer:")
    return "\n".join(lines)


def _should_refuse(chunks: list[dict]) -> bool:
    """
    Programmatic refusal: if no chunks were retrieved, or the best chunk's
    score is below the threshold, the corpus doesn't have the answer.
    """
    if not chunks:
        return True
    best = max(ch.get("score", 0.0) for ch in chunks)
    return best < MIN_SCORE_THRESHOLD


def generate(query: str, chunks: list[dict], temperature: float = 0.2) -> str:
    """One-shot generation. Returns the full answer as a string."""
    if _should_refuse(chunks):
        return REFUSAL

    user_msg = build_prompt(query, chunks)
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        options={"temperature": temperature},
    )
    answer = response["message"]["content"].strip()
    # Belt and suspenders: if the model still produced nothing, refuse.
    return answer if answer else REFUSAL


def stream_generate(
    query: str,
    chunks: list[dict],
    temperature: float = 0.2,
) -> Iterator[str]:
    """
    Streaming generation. Yields text fragments as the model produces them.
    """
    if _should_refuse(chunks):
        yield REFUSAL
        return

    user_msg = build_prompt(query, chunks)
    stream = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        options={"temperature": temperature},
        stream=True,
    )
    produced_anything = False
    for piece in stream:
        token = piece.get("message", {}).get("content", "")
        if token:
            produced_anything = True
            yield token
    if not produced_anything:
        yield REFUSAL


# --- Manual end-to-end test ---
if __name__ == "__main__":
    from src.retriever import retrieve

    test_queries = [
        "Who was Albert Einstein and what is he known for?",
        "Which famous place is located in Turkey?",
        "Compare Lionel Messi and Cristiano Ronaldo",
        "Who is the president of Mars?",
        "Tell me about a random unknown person John Doe",
    ]
    for q in test_queries:
        print("\n" + "=" * 70)
        print(f"Q: {q}")
        result = retrieve(q)
        best = max((c["score"] for c in result["chunks"]), default=0.0)
        print(f"   route: {result['route']}  |  chunks: {len(result['chunks'])}  |  best score: {best:.3f}")
        print("-" * 70)
        answer = generate(q, result["chunks"])
        print(answer)