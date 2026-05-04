# Production Deployment Recommendations

This project is a working *local* RAG. Taking it to a real production
environment serving many users requires changes across nearly every
layer. This document records what should change, why, and in what
order.

---

## TL;DR

The local-first design choices that make this project a good
educational artifact — a 3B model on CPU, a single-process Streamlit
app, in-process ChromaDB, a hand-rolled keyword router — are the
exact things that prevent it from scaling. A production deployment
would replace them with hosted or distributed equivalents while
keeping the *shape* of the pipeline (ingest → chunk → embed → retrieve
→ generate).

---

## 1. Architecture: from monolith to services

**Current.** One Python process. Streamlit serves the UI, calls into
`src/*` modules, which open ChromaDB on disk and shell out to a local
Ollama. State (chat history) lives in Streamlit session state and
disappears on reload.

**Recommended for production.**

- **Frontend** — a static React/Next.js app, served from a CDN.
  Streamlit is excellent for prototypes and demos but isn't designed
  to serve concurrent users at scale.
- **API gateway** — a lightweight FastAPI service exposing
  `/chat`, `/feedback`, and `/healthz`. Versioned (`/v1/...`).
- **Retrieval service** — separate process owning the vector store
  connection. Horizontally scalable behind a load balancer.
- **Generation service** — separate process owning the LLM. Critical
  to scale independently from retrieval, because LLM throughput is
  the bottleneck and the most expensive resource.
- **Message queue** for long-running jobs (re-indexing, large batch
  ingest). Redis Streams or Cloud Pub/Sub.
- **Object storage** for raw documents (S3 / GCS) instead of a local
  `data/` folder.

This split lets each layer scale on its own metrics: the retrieval
service on QPS, the generation service on tokens/second, the ingest
worker on documents/hour.

---

## 2. The vector store

**Current.** ChromaDB with persistent local disk. Works perfectly for
~6,000 chunks on one machine.

**Recommended.** Move to a managed or self-hosted vector database
designed for production workloads:

- **pgvector** if the team already uses PostgreSQL — keeps embeddings
  alongside operational data and avoids a new system.
- **Qdrant** or **Weaviate** for purpose-built performance,
  filtering, and replication.
- **Pinecone** or similar managed service if minimising ops cost
  matters more than control.

At the data scale of a real Wikipedia-style knowledge base
(millions of chunks), single-node ChromaDB stops being viable
around the 1–10 M chunk mark depending on machine size.

---

## 3. The embedding model

**Current.** `mxbai-embed-large` running in Ollama on the same host.

**Recommended.**

- **Dedicated embedding service** (TEI from Hugging Face, or a self-hosted
  Triton server with a tuned ONNX export). Embedding throughput on a
  small GPU is ~50–100x what we get from CPU Ollama.
- **Batched embedding** at index time. The current implementation
  embeds chunks one at a time because Ollama's Python client doesn't
  expose true batching — a real embedding server does.
- **Versioned indexes.** Switching embedders today requires deleting
  the collection. In production, write to a *new* index, validate
  it, then switch reads atomically. Never break live traffic.

---

## 4. The language model

**Current.** `llama3.2:3b` on CPU. ~5–10 seconds per typical answer.

**Recommended.**

- **GPU inference** via vLLM or TGI. Same model on a single mid-range
  GPU drops latency by 10x and supports concurrent requests.
- **Bigger model** if quality matters more than cost — `llama3.1:8b`
  or a fine-tuned domain model.
- **Streaming everywhere.** The UI already streams; make sure the
  full chain (gateway → generation service → frontend) preserves
  Server-Sent Events so users see tokens immediately.
- **Prompt caching.** The system prompt is identical across requests
  — vLLM and similar engines can cache its KV state and skip
  recomputing it on every call.

---

## 5. Ingestion and freshness

**Current.** A static list of 40 entities, fetched once.

**Recommended.**

- **Scheduled refreshes.** Wikipedia changes; a nightly job should
  re-fetch and re-embed only the entities whose `last_modified`
  timestamp is newer than the index version.
- **Incremental indexing.** Today, changing the entity list triggers
  a full rebuild. Production needs add / update / delete operations
  on individual entities without touching the rest of the index.
- **Source diversification.** Wikipedia alone is brittle. Add
  Wikidata for structured facts, official sites where reliable, and
  domain-specific sources. Tag each chunk with `source_type` so
  retrieval can up-weight authoritative sources.

---

## 6. Retrieval quality

**Current.** Single-vector top-K with rule-based routing.

**Recommended.**

- **Hybrid retrieval.** Combine BM25 (lexical) and vector (semantic)
  results with reciprocal rank fusion. Lexical search wins on
  entity-grounded queries; semantic search wins on paraphrased ones.
  Hybrid wins on both.
- **Reranking.** A small cross-encoder (e.g. `bge-reranker-base`)
  applied to the top-50 results dramatically improves the top-5
  precision for the same retrieval cost.
- **Learned routing.** Replace the keyword router with a small
  classifier trained on real query logs once they exist.
- **Query expansion.** For sparse queries, generate paraphrases or
  hypothetical answers (HyDE) and embed those alongside the original.

---

## 7. Evaluation and monitoring

**Current.** Manual smoke tests against the example queries.

**Recommended.**

- **Offline eval set.** A few hundred labelled (query, expected_answer,
  expected_sources) tuples. Run on every change to chunking, embedder,
  prompt, or retrieval logic. Metrics: retrieval recall@K, answer
  groundedness, refusal precision.
- **Online metrics.** Latency percentiles (p50/p95/p99 for retrieval
  and generation separately), token usage, refusal rate, user
  thumbs-up/down feedback.
- **LLM-as-judge** for groundedness scoring at scale, with a small
  human-labelled holdout to keep the judge honest.
- **Cost tracking.** GPU-hours per 1k queries, embedding cost per
  document, storage cost per million chunks.

---

## 8. Safety and compliance

**Current.** A grounding prompt and a low-score refusal threshold.

**Recommended.**

- **Output moderation.** A second model or rule layer that screens
  generated text for PII leakage, prompt injection responses, or
  unsafe content before returning to the user.
- **Input moderation.** Reject queries that try to override the
  system prompt or request the raw context dump.
- **Provenance.** Every answer should include the source documents
  it was grounded in, ideally with span-level citations. The current
  source panel is a stepping stone toward this.
- **Audit logs.** Store query, retrieved chunks, model version,
  prompt version, and final answer for every request — both for
  debugging and for compliance with content-licensing terms
  (Wikipedia is CC BY-SA, which has attribution requirements).

---

## 9. Reliability and operations

- **Health checks** on every service (`/healthz`).
- **Graceful degradation.** If the generation service is down, return
  the top retrieved chunks with a banner — better than a 500 error.
- **Rate limiting** per user / API key.
- **Backups** of the vector store, with regular restore drills.
- **Blue/green deployments** for index updates: build into a parallel
  collection, validate, then switch.

---

## 10. Suggested rollout order

If a team had to ship this in production starting from the current
codebase, the order I'd recommend is:

1. **Split frontend from backend.** FastAPI + a thin HTTP client
   replaces direct module calls. (Days.)
2. **Move generation off CPU.** A single GPU box running vLLM
   immediately gives 10x the throughput. (A week.)
3. **Add hybrid retrieval and a reranker.** Largest single quality
   win for the cost. (A week.)
4. **Build the offline eval harness** before changing anything else,
   so future changes are measurable. (A week.)
5. **Migrate the vector store** when data grows past single-node
   ChromaDB. (As needed.)
6. **Everything else** — moderation, audit logs, cost tracking,
   monitoring — in parallel with the above as the system gets real
   traffic.
