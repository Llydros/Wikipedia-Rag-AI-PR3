# Local Wikipedia RAG

A fully-local Retrieval-Augmented Generation system that answers
questions about famous people and famous places. The language model,
the embeddings, the vector store, and the UI all run on your own
machine. No external APIs are called.

Built for **BLG483E – Project 3**.
---
## Demo Video link: https://youtu.be/5LXFQIq2K6g
---

## What you'll need

- **Python 3.10+** (developed on 3.14)
- **Ollama** — <https://ollama.com>
- ~3 GB free disk, 8 GB RAM minimum

---

## How to install dependencies

Clone the repo and create a virtual environment:

**Windows (PowerShell):**

```powershell
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The Python dependencies are listed in `requirements.txt`:

- `chromadb` — vector store
- `ollama` — Python client for the local model
- `streamlit` — chat UI
- `wikipedia-api` — Wikipedia ingestion
- `numpy`

---

## How to run the local model

After installing Ollama, pull the two models the project uses:

```bash
ollama pull llama3.2:3b
ollama pull mxbai-embed-large
```

That's roughly 2.7 GB total. Ollama runs as a background service
once installed (system-tray icon on Windows, menu-bar icon on macOS).
You don't start it manually — the project talks to it over
`localhost:11434`.

Verify it works:

```bash
ollama list
```

You should see both model names.

---

## How to ingest data

A single command does everything: fetch the Wikipedia articles,
chunk them, embed each chunk, and write the persistent vector
store to `chroma_db/`.

```bash
python build_index.py
```

Expected runtime: **~15 minutes** on a modern CPU (a few seconds
for ingest + ~10–14 minutes for embedding ~5,800 chunks). A
progress bar shows live throughput and ETA.

The ingestion is split across two scripts under the hood — both
run automatically as part of `build_index.py`, but you can also
invoke them individually:

```bash
python -m src.ingest         # download Wikipedia articles into data/
python -m src.embed_store    # chunk + embed + index into chroma_db/
```

To re-fetch every Wikipedia article (rather than skipping ones
already on disk):

```bash
python build_index.py --force
```

---

## How to start the application

```bash
streamlit run app.py
```

Open <http://localhost:8501> in your browser. You'll see the
chat interface, a sidebar with example queries, and a panel for
retrieved sources.

---

## Example queries

**People**

- Who was Albert Einstein and what is he known for?
- What did Marie Curie discover?
- Why is Nikola Tesla famous?
- Compare Lionel Messi and Cristiano Ronaldo.

**Places**

- Where is the Eiffel Tower located?
- What is Machu Picchu?
- Where is Mount Everest?

**Mixed**

- Which famous place is located in Turkey?
- Compare Albert Einstein and Nikola Tesla.

**Out of corpus (the system should refuse)**

- Who is the president of Mars?
- Tell me about a random unknown person John Doe.

---

## Project layout

```
.
├── app.py                  Streamlit chat UI
├── build_index.py          One-command ingest + embed
├── requirements.txt        Python dependencies
├── README.md               This file
├── Product_prd.md          Product requirements
├── recommendation.md       Production deployment notes
├── src/
│   ├── config.py           Entities + settings
│   ├── ingest.py           Wikipedia ingestion script
│   ├── chunker.py          Boundary-aware chunker
│   ├── embed_store.py      Embedding + ChromaDB persistence
│   ├── retriever.py        Query routing + similarity search
│   └── generator.py        Local LLM call + grounded prompt
├── data/                   (generated) raw Wikipedia text
└── chroma_db/              (generated) vector store
```

---

## Notes

- **Vector store design.** A single ChromaDB collection holds all
  chunks, tagged with `type: person | place` metadata (Option B
  from the brief).
- **Embedder.** `mxbai-embed-large` was chosen over `nomic-embed-text`
  after the smaller model failed on entity-grounded queries like
  *"Which famous place is located in Turkey?"*.
- **Refusal.** When retrieval scores are too low or the model
  produces no output, the system replies *"I don't know based on
  the provided information."* See `Product_prd.md` for details.
