"""
Central configuration for the RAG system.
Edit ENTITIES here to change what gets ingested.
"""
from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# --- Models (must be pulled via `ollama pull`) ---
LLM_MODEL = "llama3.2:3b"
EMBED_MODEL = "mxbai-embed-large"

# --- Chunking ---
CHUNK_SIZE = 500          # characters per chunk
CHUNK_OVERLAP = 100       # characters of overlap between consecutive chunks

# --- Retrieval ---
TOP_K = 5                 # number of chunks to retrieve per query

# --- ChromaDB ---
COLLECTION_NAME = "wikipedia_rag"

# --- Entities to ingest ---
# Each entity has a Wikipedia title and a type (person | place).
# The type is stored as metadata so we can filter at query time.
ENTITIES = [
    # --- People (required minimum) ---
    {"title": "Albert Einstein", "type": "person"},
    {"title": "Marie Curie", "type": "person"},
    {"title": "Leonardo da Vinci", "type": "person"},
    {"title": "William Shakespeare", "type": "person"},
    {"title": "Ada Lovelace", "type": "person"},
    {"title": "Nikola Tesla", "type": "person"},
    {"title": "Lionel Messi", "type": "person"},
    {"title": "Cristiano Ronaldo", "type": "person"},
    {"title": "Taylor Swift", "type": "person"},
    {"title": "Frida Kahlo", "type": "person"},
    # --- People (extras to reach 20) ---
    {"title": "Isaac Newton", "type": "person"},
    {"title": "Charles Darwin", "type": "person"},
    {"title": "Mahatma Gandhi", "type": "person"},
    {"title": "Nelson Mandela", "type": "person"},
    {"title": "Mustafa Kemal Atatürk", "type": "person"},
    {"title": "Stephen Hawking", "type": "person"},
    {"title": "Vincent van Gogh", "type": "person"},
    {"title": "Pablo Picasso", "type": "person"},
    {"title": "Wolfgang Amadeus Mozart", "type": "person"},
    {"title": "Ludwig van Beethoven", "type": "person"},

    # --- Places (required minimum) ---
    {"title": "Eiffel Tower", "type": "place"},
    {"title": "Great Wall of China", "type": "place"},
    {"title": "Taj Mahal", "type": "place"},
    {"title": "Grand Canyon", "type": "place"},
    {"title": "Machu Picchu", "type": "place"},
    {"title": "Colosseum", "type": "place"},
    {"title": "Hagia Sophia", "type": "place"},
    {"title": "Statue of Liberty", "type": "place"},
    {"title": "Giza pyramid complex", "type": "place"},   # Wikipedia title for Pyramids of Giza
    {"title": "Mount Everest", "type": "place"},
    # --- Places (extras to reach 20) ---
    {"title": "Stonehenge", "type": "place"},
    {"title": "Petra", "type": "place"},
    {"title": "Christ the Redeemer (statue)", "type": "place"},
    {"title": "Acropolis of Athens", "type": "place"},
    {"title": "Angkor Wat", "type": "place"},
    {"title": "Niagara Falls", "type": "place"},
    {"title": "Mount Fuji", "type": "place"},
    {"title": "Sagrada Família", "type": "place"},
    {"title": "Chichen Itza", "type": "place"},
    {"title": "Topkapı Palace", "type": "place"},
]