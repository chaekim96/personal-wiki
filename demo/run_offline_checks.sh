#!/bin/bash
# Offline demo: the non-interactive checks, in order, with clear headers.
# Run AFTER disconnecting the internet and restarting Ollama (see demo/offline_demo.md).
# Everything is also saved to evidence/offline/run_offline_checks.txt.
cd "$(dirname "$0")/.." || exit 1
mkdir -p evidence/offline
W=.venv/bin/wiki
OLLAMA=/Applications/Ollama.app/Contents/Resources/ollama

{
step() { echo; echo "==================== $1 ===================="; }

step "0a. Internet is OFF: this request must FAIL"
date
if curl -sS --max-time 5 https://example.com -o /dev/null; then
  echo "!! NETWORK IS ON - stop and disconnect before recording"; exit 1
else
  echo "OK: internet unreachable (expected)"
fi

step "0b. Downloading a model must FAIL offline"
$OLLAMA pull gemma4:e2b-it-qat; echo "exit=$?"

step "0c. Local model server is up (localhost only) and models are on disk"
curl -s --max-time 5 http://localhost:11434/api/version; echo
$OLLAMA list

step "1. wiki --help"
$W --help

step "2. Online mode must fail visibly (local is the default)"
$W --mode online ask "What learning rate did I use in Assignment 3?"; echo "exit=$?"

step "3. Ingest a source offline"
$W ingest "./vault/raw/Wikipedia - Retrieval-augmented generation.md" --force

step "4. Ask test 1 (direct)"
$W ask "What learning rate did I use in Assignment 3?"
step "5. Ask test 2 (paraphrased)"
$W ask "Why is RAG cheaper than retraining a model when information changes?"
step "6. Ask test 3 (two sources)"
$W ask "How many attention heads did my A3 model have, and why is multi-head attention easy to parallelize?"
step "7. Ask test 4 (unsupported)"
$W ask "What validation loss did my A3 model reach at 10,000 training steps?"

step "8. Search: original passages, no answer"
$W search "positional encoding" -k 3
step "9. Standalone ask"
$W ask "What does KV caching do?"
step "10. A claim made only in chat (Jordan) must not be evidence in ask"
$W ask "Who was my A3 project partner?"

step "done"
date
} 2>&1 | tee evidence/offline/run_offline_checks.txt
