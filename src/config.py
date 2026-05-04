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
    # =========================================================
    # PEOPLE
    # =========================================================

    
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

    
    {"title": "Galileo Galilei", "type": "person"},
    {"title": "Cleopatra", "type": "person"},
    {"title": "Genghis Khan", "type": "person"},
    {"title": "Suleiman the Magnificent", "type": "person"},
    {"title": "Christopher Columbus", "type": "person"},
    {"title": "Elon Musk", "type": "person"},
    {"title": "Steve Jobs", "type": "person"},
    {"title": "Michael Jackson", "type": "person"},
    {"title": "Bruce Lee", "type": "person"},
    {"title": "Muhammad Ali", "type": "person"},
    {"title": "Serena Williams", "type": "person"},
    {"title": "Michelangelo", "type": "person"},
    {"title": "Jane Austen", "type": "person"},
    {"title": "Mary Shelley", "type": "person"},
    {"title": "Alexander the Great", "type": "person"},

    
    {"title": "Stevie Nicks", "type": "person"},
    {"title": "Ronnie James Dio", "type": "person"},
    {"title": "Klaus Meine", "type": "person"},
    {"title": "David Hume", "type": "person"},
    {"title": "Ricardo Quaresma", "type": "person"},
    

    # =========================================================
    # PLACES
    # =========================================================

    
    {"title": "Eiffel Tower", "type": "place"},
    {"title": "Great Wall of China", "type": "place"},
    {"title": "Taj Mahal", "type": "place"},
    {"title": "Grand Canyon", "type": "place"},
    {"title": "Machu Picchu", "type": "place"},
    {"title": "Colosseum", "type": "place"},
    {"title": "Hagia Sophia", "type": "place"},
    {"title": "Statue of Liberty", "type": "place"},
    {"title": "Giza pyramid complex", "type": "place"}, 
    {"title": "Mount Everest", "type": "place"},

    
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

    
    {"title": "Cappadocia", "type": "place"},
    {"title": "Santorini", "type": "place"},
    {"title": "Galápagos Islands", "type": "place"},
    {"title": "Sahara", "type": "place"},
    {"title": "Amazon rainforest", "type": "place"},
    {"title": "Yellowstone National Park", "type": "place"},
    {"title": "Times Square", "type": "place"},
    {"title": "Buckingham Palace", "type": "place"},
    {"title": "Forbidden City", "type": "place"},
    {"title": "Mount Kilimanjaro", "type": "place"},
    {"title": "Sydney Opera House", "type": "place"},
    {"title": "Uluru", "type": "place"},
    {"title": "Easter Island", "type": "place"},
    {"title": "Lake Baikal", "type": "place"},
    {"title": "Alhambra", "type": "place"},

    
    {"title": "Hungarian Parliament Building", "type": "place"},
    {"title": "Sint-Petrus-en-Pauluskerk", "type": "place"},
    {"title": "Notre-Dame de Paris", "type": "place"},
    {"title": "Roman Baths of Ankara", "type": "place"},
    {"title": "Vaduz Castle", "type": "place"},
    

    ]