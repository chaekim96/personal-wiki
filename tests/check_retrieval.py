"""Retrieval check for the 4 ask tests (see tests/ask_tests.md). Never calls Gemma; hybrid mode calls the embedding model.

For each question: run the retriever and report the rank of each expected passage
(identified by a short phrase from tests/ask_tests.md). Run: .venv/bin/python tests/check_retrieval.py [hybrid|bm25]
"""
from wiki.retrieve import Index, load_passages, tokens

K = 5  # ask mode sends the top 5 passages to Gemma
TESTS = [
    ("1 direct", "What learning rate did I use in Assignment 3?",
     ["Learning rate: 0.001"]),
    ("2 paraphrased", "Why is RAG cheaper than retraining a model when information changes?",
     ["reduces the need to retrain LLMs", "rather than having to retrain the model"]),
    ("3 two sources", "How many attention heads did my A3 model have, and why is multi-head attention easy to parallelize?",
     ["2 blocks, 4 heads", "easier to parallelize due to the use of independent heads"]),
    ("4 unsupported", "What validation loss did my A3 model reach at 10,000 training steps?",
     []),
]

import sys
METHOD = sys.argv[1] if len(sys.argv) > 1 else "hybrid"   # "hybrid" or "bm25"
index = Index(load_passages())
for name, question, needles in TESTS:
    ranked, used = index.search(question, k=len(index.passages), method=METHOD)
    print(f"\nTest {name}: {question}   [retrieval: {used}]")
    print(f"  query words: {tokens(question)}")
    for needle in needles:
        hit = next((h for h in ranked if needle in h["text"]), None)
        status = ("IN TOP 5" if hit["rank"] <= K else "MISSED (not in top 5)") if hit else "NOT FOUND"
        print(f"  expected '{needle}': rank {hit['rank'] if hit else '-'}, score {hit['score'] if hit else '-'} -> {status}")
    for h in ranked[:K]:
        print(f"    top{h['rank']}: bm25 #{h['bm25_rank']:<3} meaning #{h.get('dense_rank', '-'):<3}  {h['source'].split('/')[-1][:32]:32s} | {h['section'].split(' > ')[-1][:45]}")
