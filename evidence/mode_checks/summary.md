# Mode checks (2026-09-29, online, before the offline demo)

| Check | Expected | Actual | Result | File |
|---|---|---|---|---|
| chat: "what can we do?" | accurate capabilities, no notes search, no citations, no insufficient reply | listed brainstorm/draft/plan, follow-ups, wiki lookups with citations (named note topics), ask/search commands, and what it cannot do; routing: code rule, no search | PASS | [chat_session.txt](chat_session.txt) turn 1 |
| chat: "what can you help me with?" | same | same content, different wording; no search | PASS | turn 2 |
| chat: draft, then "make that shorter" | uses the conversation | 3-step RAG study plan, then condensed version of the same plan; no new search | PASS, but the plan was Wren's own idea and was **not labelled "Suggestion:"** | turns 3-4 |
| search "positional encoding" | original passages + paths, no answer | 3 passages from Transformer article with sections and lines; no model answer; model shown as "none (retrieval only)" | PASS | [search_positional_encoding.txt](search_positional_encoding.txt) |
| search with Ollama unreachable | still works | `retrieval: bm25 (fallback: Ollama not running)` + passages | PASS | (tested by pointing at a dead port; see Phase 4) |
| ask standalone "What does KV caching do?" | cited neutral answer | "...saves the computed key and value vectors ... [P1]"; P1 = KV caching section lines 3979-3981, near-verbatim | PASS (runs 1-4) | [ask_standalone_kv_caching*.txt](.) |
| claim made only in chat is not evidence in ask | chat: "my A3 project partner was Jordan"; ask "Who was my A3 project partner?" must not say Jordan | chat repeated Jordan from conversation context (allowed in chat). ask **never** said Jordan (runs 1-4). Run 2-3: insufficient evidence. Run 1 and final run 4: answered a different question with a real citation ("The model continues short sentences and is not a chatbot [P2]") | chat/ask separation: PASS. Insufficient-evidence behavior in final config: **FAIL** | [ask_chat_claim_jordan*.txt](.) |

Earlier chat development issue (Phase 4, before these checks): drafts about my own work invented project status
("running smoothly", "ready to move on to the evaluation phase"). Router and persona were fixed so drafts now search
notes and cite them, but "ready for evaluation" still appeared in later runs: a known chat limitation.
