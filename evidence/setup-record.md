# Setup record (Phase 1, 2026-09-29)

## Device
- macOS 15.7.4 (24G517), Apple M3 Pro, 18-core GPU (Metal 3)
- 18 GB unified memory; free 29–34% (memory_pressure) with usual apps open
- Disk: 17 GiB free before downloads, 12 GiB after

## Runtime
- Ollama 0.35.0 (`/Applications/Ollama.app`, from github.com/ollama/ollama/releases/download/v0.35.0/Ollama.dmg)
- Signed: Developer ID Application: Infra Technologies, Inc (3MU9H2V9Y9); Gatekeeper: accepted, Notarized

## Model
- Ollama tag: `gemma4:e2b-it-qat`  (ID 07ea59a47401, 4.3 GB on disk)
- Google name: Gemma 4 E2B, instruction-tuned, quantization-aware trained
- `ollama show`: architecture gemma4, parameters 4.6B, quantization Q4_0, context length 131072, requires 0.30.5
- Tokenizer is inside the GGUF model file (no separate download)
- Official memory table (ai.google.dev/gemma/docs/core): E2B Q4_0 = 2.9 GB to load

## Smoke test (local, num_ctx 8192, think=false)
- Prompt "Reply with exactly: ready" -> 'ready'
- load 5.40 s, total 5.65 s
- `ollama ps`: SIZE 1.7 GB, 100% GPU, CONTEXT 8192
