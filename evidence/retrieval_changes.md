# Retrieval changes (measured with tests/check_retrieval.py, top 5 passages go to Gemma)

## v1: BM25 keyword search (2026-09-29) - `retrieval_check_v1_bm25.txt`
| Test | Expected passage | Rank |
|---|---|---|
| 1 direct | README "Learning rate: 0.001" | 1 |
| 2 paraphrased | RAG "reduces the need to retrain" / "rather than having to retrain" | 5 / 4 (barely in top 5) |
| 3 two sources | Transformer "independent heads" / README "2 blocks, 4 heads" | 1 / **25 (missed)** |
| 4 unsupported | (none expected; README loss passages retrieved) | - |

Diagnosis for Test 3: "A3" appears 0 times in any source (the README says "Assignment 3"), and the
"multi-head attention ... parallelize" half matches many Transformer passages, crowding out the README.

## v2: hybrid = BM25 + embeddinggemma:latest, Reciprocal Rank Fusion (k=60) - `retrieval_check_v2_hybrid.txt`
Change: added local embeddings (embeddinggemma:latest, 307.58M params, BF16, 768-dim), EmbeddingGemma
query/document prefixes from ai.google.dev, merged with BM25 by RRF. Falls back to BM25 when Ollama is off.

| Test | Rank v1 -> v2 |
|---|---|
| 1 | 1 -> 1 |
| 2 | 5 / 4 -> **2 / 3** (improved) |
| 3 | 1 / 25 -> 1 / **28 (still missed)** |

My expectation that meaning-based search would bridge "A3" and "Assignment 3" was wrong.
Extra diagnosis: the first half alone ("How many attention heads did my A3 model have") puts the
expected README passage at rank 9 (hybrid) / 10 (BM25), while the README "trap" passage
"(one of 8 attention heads)" ranks 2. So splitting the question would not fix it either.
