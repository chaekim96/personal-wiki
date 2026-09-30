# Ask-mode tests (written 2026-09-29, before any retrieval code existed)

This file is the answer key. It lives outside `vault/` so the retriever can never find it.
Each test is run with `wiki ask "<question>"` (local mode, no chat history).

Source paths are relative to `vault/raw/`.

---

## Test 1: direct (one source)

**Question:** What learning rate did I use in Assignment 3?

**Expected source:** `Custom LLM Assignment README.md`, section "2. My three choices and prediction"

**Expected passage:**
> **Learning rate: 0.001.** That is large enough to make progress within 3,000 steps and small enough
> to avoid overshooting. The notebook warms the rate up over the first 100 steps and then
> cosine-decays it to 10% of the peak.

**Expected behavior:** Answers 0.001. May add the 100-step warmup and cosine decay to 10%.
Cites the README passage above.

**Fail if:** wrong number, no citation, or a citation that points to a passage that was not retrieved.

---

## Test 2: paraphrased (wording differs from the source)

**Question:** Why is RAG cheaper than retraining a model when information changes?

**Expected source:** `Wikipedia - Retrieval-augmented generation.md`, intro and section "Process"

**Expected passages:**
> RAG also reduces the need to retrain LLMs with new data, saving on computational and financial costs.

> when new information becomes available, rather than having to retrain the model, all that's needed
> is to augment the model's external knowledge base with the updated information ("augmentation").

**Expected behavior:** Explains that new information is added to an external knowledge base
instead of retraining the model, which saves compute and money. Cites the RAG article.

**What this tests:** the question says "retraining", "cheaper", "information changes"; the source says
"retrain", "computational and financial costs", "new information". Keyword retrieval may miss this.
If the right passage is not retrieved, fix retrieval (e.g. stemming or embeddings) before judging the model.

---

## Test 3: combines two sources

**Question:** How many attention heads did my A3 model have, and why is multi-head attention easy to parallelize?

**Expected sources:**
1. `Custom LLM Assignment README.md`, opening paragraph
   > A tiny word-level language model: Karpathy's **nanoGPT** (2 blocks, 4 heads,
   > 64-number embeddings, 48-token context)
2. `Wikipedia - Transformer architecture.md`, section "History > Parallelizing attention"
   > This led to the introduction of a multi-head attention model that was easier to parallelize
   > due to the use of independent heads and the lack of recurrence.

**Expected behavior:** 4 heads (per block; 2 blocks). Multi-head attention parallelizes because the
heads are independent and there is no recurrence. Cites **both** sources.

**Known trap:** README section 5 says "(one of 8 attention heads)", i.e. 2 blocks x 4 heads.
An answer of "8 heads total" is acceptable only if it explains 2 x 4; an answer that contradicts
the README without explanation fails.

---

## Test 4: plausible but unsupported

**Question:** What validation loss did my A3 model reach at 10,000 training steps?

**Expected source:** none. Both runs stopped at 3,000 steps (README sections 2 and 3).

**Expected behavior:** An explicit insufficient-evidence response, e.g. "The sources do not say;
the runs only went to 3,000 steps." It may mention the 3,000-step limit with a citation.

**Fail if:** it reports any number (e.g. 0.706 or 0.949) as the 10,000-step validation loss,
or answers from general knowledge.

---

## Results

Recorded per run in `evidence/` (question, retrieved passages and paths, model, mode, answer,
citations, and my assessment). Earlier failed runs are kept, not overwritten.
