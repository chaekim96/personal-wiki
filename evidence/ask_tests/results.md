# Ask-mode test results (2026-09-29, online, before the offline demo)

## Final configuration = run 4 (see [config_runs.md](config_runs.md) for runs 1-4 and why)

| Test | Answer (run 4) | Claim check | Verdict |
|---|---|---|---|
| 1 direct | "The learning rate used was 0.001 [P1]." | P1 README lines 45-54 "**Learning rate: 0.001.**" | **PASS** |
| 2 paraphrased | "RAG reduces the need to retrain LLMs with new data, which saves on computational and financial costs [P2]." | P2 RAG Introduction lines 8-10, near-verbatim | **PASS** (knowledge-base point not used) |
| 3 two sources | "The smallest GPT-2 model has 12 attention heads [P2]. Multi-head attention is easier to parallelize because the computations for each attention head can be performed in parallel ... [P2]." | P2 does say GPT-2 has n_head=12 and that head computations run in parallel, but GPT-2 is **not my A3 model**: a nearby fact answering a different question. README "2 blocks, 4 heads" was never retrieved. | **FAIL** |
| 4 unsupported | Insufficient evidence; note: 0.706 / 0.949 "at 3,000 training steps ... does not state the validation loss at 10,000" | P2 loss table rows at 3,000 steps | **PASS** |

Files: [test1_run4](test1_run4.txt) · [test2_run4](test2_run4.txt) · [test3_run4](test3_run4.txt) · [test4_run4](test4_run4.txt)
· JSON: `../runs/20260929_2048{44_858,47_168,50_680,54_332}_ask.json`

---

## Run 1 details (original setting, kept as evidence)

Model `gemma4:e2b-it-qat` (Q4_0) via Ollama 0.35.0 · mode local · retrieval hybrid (BM25 + `embeddinggemma:latest`, RRF k=60) · top 5 passages · temperature 0.
Expected behavior for each test was written first in [tests/ask_tests.md](../../tests/ask_tests.md).
Method: inspect retrieval first, then check each claim against the passage it cites (full passages are in the JSON files).

| Test | Retrieval | Answer | Verdict |
|---|---|---|---|
| 1 direct | expected passage = P1 | 0.001 [P1] | **PASS** |
| 2 paraphrased | both expected passages retrieved (P2, P3) | cites P2 correctly; omits the knowledge-base point | **PASS (partial detail)** |
| 3 two sources | README "2 blocks, 4 heads" **not retrieved**; trap passage retrieved | "8 heads", wrong citation | **FAIL** |
| 4 unsupported | tempting 3,000-step loss passages retrieved | insufficient evidence; 3,000-step values labelled correctly | **PASS** |

---

## Test 1: direct
- **Question:** What learning rate did I use in Assignment 3?
- **Retrieved:** P1 README "2. My three choices and prediction" lines 45-54 (**expected passage**); P2 README "3. My runs" line 103; P3 README "3. My runs" 83-95; P4 README "5. Evidence..." 202-204; P5 README "2. My three choices..." 65-74
- **Answer:** "The learning rate used was 0.001 [P1]."
- **Citation check (code):** answered, no problems
- **Claim check (me):** P1 contains "**Learning rate: 0.001.**" Supported.
- **Verdict:** PASS
- **Files:** [terminal](test1_run1.txt) · [JSON](../runs/20260929_204553_357_ask.json) · 3.21 s total (generate 2.79 s)

## Test 2: paraphrased
- **Question:** Why is RAG cheaper than retraining a model when information changes?
- **Retrieved:** P1 RAG "Challenges" 73-74; **P2 RAG "Introduction" 8-10 (expected)**; **P3 RAG "Process" 20 (expected)**; P4 "RAG poisoning" 78-79; P5 "RAG and LLM limitations" 15-16
- **Answer:** "RAG reduces the need to retrain LLMs with new data, which saves on computational and financial costs [P2]."
- **Citation check (code):** answered, no problems
- **Claim check (me):** P2 contains "RAG also reduces the need to retrain LLMs with new data, saving on computational and financial costs." Supported, near-verbatim.
- **Gap:** the expected second point (P3: "augment the model's external knowledge base" instead of retraining) was retrieved but not used.
- **Verdict:** PASS, with a less complete answer than expected
- **Files:** [terminal](test2_run1.txt) · [JSON](../runs/20260929_204555_669_ask.json) · 2.23 s total

## Test 3: two sources
- **Question:** How many attention heads did my A3 model have, and why is multi-head attention easy to parallelize?
- **Retrieved:** **P1 Transformer "Parallelizing attention" 36-37 (expected)**; P2 Transformer "Multihead attention" 1777; P3 "Multi-Query Attention"; P4 "FlashAttention"; P5 README "5. Evidence..." 224-235 (the **trap** passage: "(one of 8 attention heads)").
  The expected README passage "2 blocks, 4 heads" was **not retrieved** (rank 28, see [retrieval_changes.md](../retrieval_changes.md)).
- **Answer:** "The A3 model had 8 attention heads, and multi-head attention is easier to parallelize because the computations for each attention head can be performed in parallel [P2]."
- **Citation check (code):** answered, no problems. **This shows the limit of the code check**: P2 was retrieved, so the label is valid, but P2 does not support the first claim.
- **Claim check (me):**
  - "8 attention heads": comes from P5 ("one of 8 attention heads"), is cited to P2 (a Wikipedia passage that says nothing about my model), and does not explain 2 blocks x 4 heads. **Unsupported citation; fails the test's trap rule.**
  - "computations for each attention head can be performed in parallel": P2 says "The computations for each attention head can be performed in parallel, which allows for fast processing." Supported. (The expected P1 reason, "independent heads and the lack of recurrence", was retrieved but not used.)
- **Verdict:** FAIL. Root cause is retrieval (my shorthand "A3" is not in any source; the Transformer article crowds out the README), plus a mis-attributed citation by the model.
- **Decision:** kept as the documented limitation (no setting changed). Proposed improvement: an alias file ("A3 = Assignment 3 = Custom LLM") for query expansion, and a rule that guarantees each source's best passage a slot in the top 5; plus a claim-level check that the cited passage contains the key numbers of the claim.
- **Files:** [terminal](test3_run1.txt) · [JSON](../runs/20260929_204559_110_ask.json) · 3.38 s total

## Test 4: unsupported
- **Question:** What validation loss did my A3 model reach at 10,000 training steps?
- **Retrieved:** P1 README "3. My runs" 83-95; P2 README "4. Evidence: samples and loss" 138-169 (loss table); P3 README "2. My three choices" 45-54; P4 README "4. ..." 171; P5 README "5. ..." 224-235. All plausible-looking, none about 10,000 steps.
- **Answer (displayed):** "Insufficient evidence: the retrieved passages do not answer this question." Model's note: "The validation loss for Experiment 1 at 3,000 training steps was 0.706 [P2]. The validation loss for Experiment 2 at 3,000 training steps was 0.949 [P2]."
- **Citation check (code):** insufficient, no problems
- **Claim check (me):** P2 table rows "| 1: starter | 3,000 | 0.678 | 0.706 |" and "| 2: expanded | 3,000 | 0.762 | 0.949 |". The note's numbers are correct and correctly labelled as 3,000-step values; it does not present them as the 10,000-step answer.
- **Verdict:** PASS (no initial failure to document)
- **Files:** [terminal](test4_run1.txt) · [JSON](../runs/20260929_204602_663_ask.json) · 3.49 s total
