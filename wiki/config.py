"""All paths and settings in one place, so every other file imports from here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the personal-wiki/ folder

# The Obsidian vault (the only folder a human browses)
VAULT = ROOT / "vault"
RAW = VAULT / "raw"            # original sources, never modified
WIKI = VAULT / "wiki"          # generated + reviewed notes
INDEX_MD = VAULT / "index.md"  # human landing page
TOPIC_FOLDERS = ["Concepts", "Projects"]

# Machine files live OUTSIDE the vault
DATA = ROOT / "data"
CATALOG = DATA / "catalog.json"   # source ID -> original file + generated notes
CHUNKS = DATA / "chunks.jsonl"    # retrieval passages (one JSON object per line)
EMBEDDINGS = DATA / "embeddings.json"  # one meaning-vector per passage (for hybrid search)
PROMPTS = ROOT / "prompts"
EVIDENCE = ROOT / "evidence"

# Chunking
PASSAGE_WORDS = 250          # target size of one retrieval passage
MIN_PASSAGE_WORDS = 40       # smaller leftovers are merged into the next passage
SKIP_SECTIONS = {"References", "See also", "Notes", "Further reading", "External links"}

# Local model (Ollama)
OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e2b-it-qat"
NUM_CTX = 8192               # context window we ask Ollama for (tokens)
EMBED_MODEL = "embeddinggemma:latest"  # local embedding model for hybrid search (307M params, BF16)
RRF_K = 60                   # rank-fusion constant: fused score = sum of 1 / (RRF_K + rank)
