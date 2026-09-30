# Offline demo (2026-09-29, 21:21-21:25 PDT)

Setup: Wi-Fi off, Ollama quit and reopened, new terminal. The session was recorded as
`offline_demo.m4v` (214 s). That file is compressed to 752x1080 H.264 with macOS `avconvert`, because the
original .mov was 108 MB, over GitHub's 100 MB limit. The text transcript is `terminal_session.txt` (from `script`).
The Claude app visible in the recording also shows "Request failed · Retrying", another sign the internet was off.

| Step | Result (see [run_offline_checks.txt](run_offline_checks.txt)) |
|---|---|
| Internet off | `curl https://example.com`: "Could not resolve host" |
| Network use fails visibly | `ollama pull gemma4:e2b-it-qat`: "dial tcp: lookup registry.ollama.ai: no such host", exit=1 |
| Local runtime | `{"version":"0.35.0"}` on localhost; `ollama list` shows both models on disk |
| `wiki --help` | printed |
| `wiki --mode online ...` | "error: online mode is not configured", exit=2 |
| Ingest a source | RAG source re-ingested, 1 WRITE call (7.72 s) + 1 LINK call, all 7 reviewed notes kept, 10.16 s total |
| Ask test 1 | "The learning rate used was 0.001 [P1]." PASS. Retrieval took 20.06 s: first load of the embedding model after the restart |
| Ask test 2 | "RAG reduces the need to retrain LLMs ... [P2]." PASS |
| Ask test 3 | "The smallest GPT-2 model has 12 attention heads [P2] ..." FAIL (same as the online run) |
| Ask test 4 | "Insufficient evidence ..." with 3,000-step values labelled. PASS |
| Search "positional encoding" | 3 passages with paths and lines, no answer |
| Standalone ask (KV caching) | cited answer [P1]. PASS |
| Ask "Who was my A3 project partner?" | did not say Jordan; answered a different question ("not a chatbot [P2]"), same as online run 4 |

All offline answers are identical to the final online run (run 4).

## Chat offline, and a gap
Chat ran offline in the same session (`terminal_session.txt`, 3 turns saved in `../runs/20260929_2123*_chat.json`):
drafting a note and a to-do list for another class. Routing, persona, and conversation context worked, and there
were no notes searches for these general requests.
**Gap:** the required chat mode checks ("what can we do?", "what can you help me with?", draft then
"make that shorter", and stating the "Jordan" claim in chat) were **not** repeated offline. They were run online
with the same code and models ([../mode_checks/](../mode_checks/)). The Jordan `ask` above was run offline,
but in this offline session the claim was never stated in chat.

Small issue seen offline: "hello can you draft a note" was routed as a greeting by the code rule, because it
starts with "hello". It did not change the reply here (no notes were needed).
**Fixed after the demo** (commit "Fix chat greeting rule"): the rule now only matches a message that is just a
greeting ("hello", "thanks wren"). A re-run (online) routed "hello can you draft a note" to the router model
([../runs/20260929_213830_348_chat.json](../runs/20260929_213830_348_chat.json)).
