# Offline demo checklist

Goal: prove that ingestion, the 4 ask tests, and the chat/search mode checks run with the internet disconnected.
Everything below is done by me on my own Mac. Expected total time: about 10 minutes.

## Before disconnecting (while online)
1. Confirm the models are on disk:
   `/Applications/Ollama.app/Contents/Resources/ollama list` shows `gemma4:e2b-it-qat` and `embeddinggemma:latest`.
2. Close other heavy apps.

## Disconnect and restart
3. Turn **Wi-Fi off** (menu bar) and unplug any Ethernet / phone hotspot.
4. **Quit Ollama** (menu-bar llama icon -> Quit Ollama), then open `/Applications/Ollama.app` again.
5. **Quit Terminal** and open a **new** Terminal window (a fresh CLI session).

## Start recording
6. Press **Cmd+Shift+5**, choose "Record Selected Portion" around the Terminal window, click Record.
7. Also capture a text transcript of the whole session:
   ```bash
   cd ~/Desktop/personal-wiki
   script evidence/offline/terminal_session.txt
   ```

## Run the demo (inside the recording)
8. Show the network is off: `curl -sS --max-time 5 https://example.com` must print an error.
9. Chat mode checks. Run `.venv/bin/wiki chat` and type these lines one at a time:
   ```
   what can we do?
   what can you help me with?
   draft a 3-step study plan for learning how RAG works
   make that shorter
   by the way, my A3 project partner was Jordan
   /exit
   ```
10. Everything else in one go (network failure, --help, online-mode failure, ingest, the 4 ask tests,
    search, standalone ask, and the "Jordan" ask):
    ```bash
    bash demo/run_offline_checks.sh
    ```
11. Type `exit` to end the `script` transcript. Stop the screen recording (stop button in the menu bar).

## After (can reconnect now)
12. Save the screen recording as `evidence/offline/offline_demo.mov` (or upload it and link it in the README if it is too large for GitHub, >100 MB).
13. The run files are already saved: `evidence/offline/run_offline_checks.txt`, `evidence/offline/terminal_session.txt`,
    and one JSON per run in `evidence/runs/` (each says `"execution": "local"`).
14. Compare the offline answers with `evidence/ask_tests/results.md`. If an answer differs, record the offline result as-is.
