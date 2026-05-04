"""
Streamlit chat UI for the local Wikipedia RAG.

Run with:
    streamlit run app.py

Layout:
    - Sidebar: model info, controls (reset chat, show sources toggle).
    - Main: chat history with streaming answers.
    - Each assistant message has an expandable "Sources" panel and a
      latency line (retrieval ms + generation ms).
"""
import time

import streamlit as st

from src.config import LLM_MODEL, EMBED_MODEL, TOP_K
from src.retriever import retrieve
from src.generator import stream_generate


# ----- Page setup -----
st.set_page_config(
    page_title="Local Wikipedia RAG",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Local Wikipedia RAG")
st.caption(
    "Ask about famous people and places. Everything runs locally — "
    f"LLM: `{LLM_MODEL}`, embeddings: `{EMBED_MODEL}`."
)

# ----- Session state -----
# `messages` is a list of dicts:
#   {"role": "user", "content": str}
#   {"role": "assistant", "content": str, "sources": [...], "timing": {...}, "route": str}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_sources" not in st.session_state:
    st.session_state.show_sources = True


# ----- Sidebar -----
with st.sidebar:
    st.header("System")
    st.markdown(f"**LLM:** `{LLM_MODEL}`")
    st.markdown(f"**Embeddings:** `{EMBED_MODEL}`")
    st.markdown(f"**Top-K:** `{TOP_K}`")
    st.divider()

    st.header("Controls")
    st.session_state.show_sources = st.checkbox(
        "Show retrieved sources",
        value=st.session_state.show_sources,
    )
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.header("Try these")
    examples = [
        "Who was Albert Einstein and what is he known for?",
        "Where is Mount Everest?",
        "Compare Lionel Messi and Cristiano Ronaldo",
        "Which famous place is located in Turkey?",
        "Who is the president of Mars?",
    ]
    # Clicking an example loads it into the chat input via session state.
    for i, ex in enumerate(examples):
        if st.button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state.pending_query = ex
            st.rerun()


def render_sources(sources: list[dict]) -> None:
    """Render the source chunks used for an answer in an expander."""
    with st.expander(f"📎 Sources ({len(sources)} chunks)"):
        for i, ch in enumerate(sources, 1):
            st.markdown(
                f"**[{i}] {ch['title']}**  "
                f"`type={ch['type']}`  `score={ch['score']:.3f}`"
            )
            st.caption(ch["text"])


def render_timing(route: str, t_retr_ms: float, t_gen_ms: float) -> None:
    """Show route + latency line under an assistant message."""
    st.caption(
        f"🧭 route: **{route}**   ·   "
        f"⏱ retrieval: {t_retr_ms:.0f} ms   ·   "
        f"generation: {t_gen_ms:.0f} ms"
    )


# ----- Render existing chat history -----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if st.session_state.show_sources and msg.get("sources"):
                render_sources(msg["sources"])
            timing = msg.get("timing", {})
            if timing:
                render_timing(
                    msg.get("route", "?"),
                    timing.get("retrieval_ms", 0),
                    timing.get("generation_ms", 0),
                )


# ----- Handle a new user query -----
# Either typed in the chat input, or loaded from a sidebar example.
prompt = st.chat_input("Ask a question about a famous person or place...")
if not prompt and "pending_query" in st.session_state:
    prompt = st.session_state.pop("pending_query")

if prompt:
    # Show user message immediately.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieve.
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("_retrieving..._")

        t0 = time.time()
        retrieval = retrieve(prompt)
        t_retr_ms = (time.time() - t0) * 1000

        # Stream the answer.
        accumulated = ""
        t1 = time.time()
        for token in stream_generate(prompt, retrieval["chunks"]):
            accumulated += token
            placeholder.markdown(accumulated + " ▌")
        t_gen_ms = (time.time() - t1) * 1000
        placeholder.markdown(accumulated)

        # Sources + timing under the answer.
        if st.session_state.show_sources:
            render_sources(retrieval["chunks"])
        render_timing(retrieval["route"], t_retr_ms, t_gen_ms)

    # Persist assistant message in history.
    st.session_state.messages.append({
        "role": "assistant",
        "content": accumulated,
        "sources": retrieval["chunks"],
        "route": retrieval["route"],
        "timing": {"retrieval_ms": t_retr_ms, "generation_ms": t_gen_ms},
    })