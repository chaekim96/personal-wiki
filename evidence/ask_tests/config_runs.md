# Ask-mode setting changes after failures (2026-09-29, same model, retrieval, and questions)

All earlier results are kept: `testN_runR.txt` here, `../mode_checks/*_runR.txt`, and the JSON in `../runs/`.
Only `prompts/wiki-instructions.md` and the JSON field order in `wiki/ask.py` changed between runs.

| Run | Setting | Jordan (claim only in chat) | KV caching | T1 | T2 | T3 | T4 |
|---|---|---|---|---|---|---|---|
| 1 | original rules; JSON order insufficient, answer, citations | answered a **different question** (corpus facts) | ok | ok | ok | **"8 heads"**, wrong citation | ok |
| 2 | + "does any passage state the answer to THIS exact question? ... never answer a different question" | **insufficient** | ok | ok | **insufficient** (regression; correct answer appears in the note) | insufficient (honest, but half was answerable) | ok |
| 3 | rule reworded: "may use different words ... that still counts" | insufficient | ok | ok | insufficient (same regression) | insufficient | ok |
| 4 | run 3 rules + JSON order answer, citations, insufficient (answer first, then judge) | answered a **different question** ("not a chatbot") | ok | ok | ok | **"smallest GPT-2 has 12 heads"**: nearby fact presented as the answer | ok |

Score per run (6 checks): run 1 = 4/6, run 2 = 4/6, run 3 = 4/6, run 4 = 4/6.

## What this shows
- The claim made only in chat ("Jordan") was **never** used by ask in any run: ask has no chat history.
- With the 2B-effective model, "should I say insufficient?" trades off against "answer paraphrased questions":
  deciding first makes it over-cautious (T2), answering first makes it answer the wrong question (Jordan, T3).
- The code citation check cannot catch an answer to a different question when the citation is real
  (Jordan run 1 and 4, T3 run 4). It only proves the label points to a retrieved passage.

## Decision (2026-09-29): keep run 4
Chosen by me: answer-first JSON order with the run-3 rule wording. It passes T1, T2, T4 (and the KV caching
standalone ask); it fails T3 and the Jordan check by answering a nearby/different question with a real citation.
Not tried: a second "does this answer the question?" judge call in the harness (proposed as a future improvement).
