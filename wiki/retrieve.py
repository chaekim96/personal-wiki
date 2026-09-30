"""The retrieval tool: find the raw passages that best match a query. The chat model is never used.

Hybrid search = two rankings merged:
  1. BM25 (keywords): a passage scores higher when it contains the query's words, especially
     words that are rare across all passages. Pure Python, always available.
  2. Embeddings (meaning): the local embedding model turns the query and every passage into
     vectors; passages whose vector points the same way as the query's rank higher. This catches
     matches with different wording ("retraining" vs "retrain", "my A3 model" vs "Assignment 3").
The two rankings are merged with Reciprocal Rank Fusion: score = sum of 1 / (RRF_K + rank).
If Ollama is not running, search falls back to BM25 only and says so.

Passage vectors are computed once at ingest time (data/embeddings.json); only the query is
embedded at search time.
"""
import hashlib
import json
import math
import re
from collections import Counter

from . import config, llm

K1, B = 1.5, 0.75   # standard BM25 settings: term-frequency saturation, length normalisation
STOPWORDS = set("""a an and are as at be by did do does for from had has have how i if in into is it its
me my of on or our so than that the their them then there these this to was we were what when where
which who why will with you your""".split())


def tokens(text: str) -> list[str]:
    """Lowercase words and numbers, minus common stopwords."""
    return [w for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower()) if w not in STOPWORDS]


def load_passages() -> list[dict]:
    if not config.CHUNKS.exists():
        raise FileNotFoundError(f"No retrieval index at {config.CHUNKS.relative_to(config.ROOT)}. "
                                "Run `wiki ingest ./vault/raw` first.")
    with open(config.CHUNKS, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# ---------- embeddings ----------

def _doc_text(p: dict) -> str:
    return f"title: {p['section']} | text: {p['text']}"      # EmbeddingGemma document format


def _hash(p: dict) -> str:
    return hashlib.sha1(_doc_text(p).encode()).hexdigest()


def build_embeddings(passages: list[dict]) -> int:
    """Embed every passage (re-using vectors for unchanged passages). Returns how many were new."""
    old = {}
    if config.EMBEDDINGS.exists():
        saved = json.loads(config.EMBEDDINGS.read_text())
        if saved.get("model") == config.EMBED_MODEL:
            old = saved["vectors"]
    todo = [p for p in passages if _hash(p) not in old]
    for i in range(0, len(todo), 16):                          # small batches
        batch = todo[i:i + 16]
        for p, v in zip(batch, llm.embed([_doc_text(p) for p in batch])):
            old[_hash(p)] = v
    keep = {_hash(p): old[_hash(p)] for p in passages}
    config.EMBEDDINGS.write_text(json.dumps({"model": config.EMBED_MODEL, "vectors": keep}))
    return len(todo)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1)


# ---------- the index ----------

class Index:
    def __init__(self, passages: list[dict]):
        self.passages = passages
        # BM25 statistics. The section heading is indexed too.
        self.docs = [Counter(tokens(p["section"] + " " + p["text"])) for p in passages]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / len(self.lengths)
        df = Counter(w for d in self.docs for w in d)          # in how many passages each word appears
        n = len(passages)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}
        # passage vectors (None if embeddings were never built)
        self.vectors = None
        if config.EMBEDDINGS.exists():
            saved = json.loads(config.EMBEDDINGS.read_text())
            if saved.get("model") == config.EMBED_MODEL:
                self.vectors = [saved["vectors"].get(_hash(p)) for p in passages]

    def bm25(self, query_words: list[str], i: int) -> float:
        doc, length, s = self.docs[i], self.lengths[i], 0.0
        for w in query_words:
            tf = doc.get(w, 0)
            if tf:
                s += self.idf[w] * tf * (K1 + 1) / (tf + K1 * (1 - B + B * length / self.avg_len))
        return s

    def search(self, query: str, k: int = 5, method: str = "hybrid") -> tuple[list[dict], str]:
        """Return (top-k passages with scores and ranks, method actually used)."""
        n = len(self.passages)
        q = tokens(query)
        bm = [self.bm25(q, i) for i in range(n)]
        bm_rank = {i: r for r, i in enumerate(sorted(range(n), key=lambda i: -bm[i]), 1)}

        dense, used, note = None, "bm25", ""
        if method == "hybrid":
            if self.vectors is None or any(v is None for v in self.vectors):
                note = "embeddings missing (run `wiki ingest ./vault/raw`)"
            else:
                try:
                    qv = llm.embed([f"task: search result | query: {query}"])[0]
                    dense = [_cosine(qv, v) for v in self.vectors]
                    used = "hybrid"
                except llm.ModelUnavailable:
                    note = "Ollama not running"
        if used == "hybrid":
            dn_rank = {i: r for r, i in enumerate(sorted(range(n), key=lambda i: -dense[i]), 1)}
            fused = {i: 1 / (config.RRF_K + bm_rank[i]) + 1 / (config.RRF_K + dn_rank[i]) for i in range(n)}
            order = sorted(range(n), key=lambda i: -fused[i])
        else:
            order = [i for i in sorted(range(n), key=lambda i: -bm[i]) if bm[i] > 0]

        hits = []
        for r, i in enumerate(order[:k], 1):
            h = {**self.passages[i], "rank": r, "bm25": round(bm[i], 3), "bm25_rank": bm_rank[i]}
            if used == "hybrid":
                h.update(score=round(fused[i], 5), cosine=round(dense[i], 4), dense_rank=dn_rank[i])
            else:
                h["score"] = round(bm[i], 3)
            hits.append(h)
        return hits, used + (f" (fallback: {note})" if note else "")


def search(query: str, k: int = 5) -> tuple[list[dict], str]:
    return Index(load_passages()).search(query, k)
