# Peak memory and response time (measured 2026-09-29, online, before the offline demo)

Device: Apple M3 Pro, 18 GB unified memory, macOS 15.7.4. Model `gemma4:e2b-it-qat` (Q4_0) + `embeddinggemma:latest` via Ollama 0.35.0.
Method: [tests/measure.py](../../tests/measure.py). Physical footprint of every Ollama process sampled once per
second with streaming `top` (this is Activity Monitor's "Memory"; it includes GPU/Metal memory on Apple Silicon),
plus a `footprint` breakdown at the end of each run, because the model weights are memory-mapped from disk
("mapped file") and are NOT counted in the footprint. CLI process measured with `/usr/bin/time -l`.
"Cold" = both models unloaded first with `ollama stop`, so loading is included.

| Run | Wall time | Gemma process peak footprint | + memory-mapped weights (end of run) | Embedding process | CLI (Python) max RSS | System free (memory_pressure) before -> after |
|---|---|---|---|---|---|---|
| Ingestion, cold: `wiki ingest ./vault/raw --force` (3 sources, 7 notes, 14 Gemma calls*) | **96.02 s** | **1,686 MB** | 3,178 MB | not loaded (all 95 passage vectors cached) | 27.0 MB | 50% -> 19% |
| One answer, cold: `wiki ask "What learning rate did I use in Assignment 3?"` | **8.42 s** | 1,305 MB | 1,938 MB | 104 MB (+587 MB mapped) | 28.8 MB | 48% -> 18% |
| One answer, warm (models already loaded) | **4.38 s** | 1,699 MB | 3,178 MB | 107 MB (+578 MB mapped) | 29.1 MB | 18% -> 18% |

\* 7 WRITE + 7 LINK calls, counted from the run log (plans were saved, so no PLAN calls).

Reading the numbers:
- Working memory of the model process peaked at ~1.7 GB; the Q4_0 weights file (3.35 GB model + 0.99 GB vision projector
  on disk) is read through memory mapping, ~3.2 GB of which was resident at the end of a run.
  So the practical total while answering is roughly 1.7 GB + 3.2 GB + 0.7 GB (embeddings) = ~5.6 GB, of 18 GB.
- `ollama ps` reported 1.7 GB for the same model; `ps` RSS reported 2.43 GB earlier. Different tools count
  mapped files differently, which is why I report footprint and mapped file separately.
- One unexplained observation: a long-running Gemma process earlier in the day showed a 5,576 MB footprint
  (`footprint` / `top`). I could not reproduce it in these runs.
- Earlier, less reliable attempt (`top -l 1` every ~3 s, 30 samples in 90 s) is kept in `v1_top_3s/`.

Files: [ingest_cold.json](ingest_cold.json) · [ask_cold.json](ask_cold.json) · [ask_warm.json](ask_warm.json)
