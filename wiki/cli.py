"""The `wiki` command. Parses the terminal command and hands off to the right part of the harness."""
import argparse
import sys
import textwrap
from pathlib import Path

from . import config, llm

HELP = f"""\
Personal wiki CLI: local Gemma + RAG over my own notes.

model: {config.MODEL} via Ollama at {config.OLLAMA_URL}
mode:  local (default; nothing leaves this computer)

commands:
  wiki ingest ./vault/raw     read raw sources, have local Gemma write linked wiki notes,
                              rebuild vault/index.md and the retrieval passages
  wiki chat                   talk with Wren, your study partner (persona in prompts/persona.md);
                              remembers recent turns, searches notes only when needed
  wiki ask "question"         standalone factual answer from your sources, with checked
                              citations, or an explicit insufficient-evidence reply
                              (no chat history, no persona; uses prompts/wiki-instructions.md)
  wiki search "query" [-k 5]  show the best-matching original passages and their paths
                              (no Gemma call; hybrid keyword + meaning search,
                              keyword-only if Ollama is off)
  wiki rename "Old" "New"     rename a note (or merge it into an existing note); keeps
                              links, index, and the source->note mapping in sync
  wiki --help                 this message

files:
  vault/raw/        original sources (never modified)
  vault/wiki/       generated notes (review and fix them here)
  data/             catalog.json (source IDs -> notes) and chunks.jsonl (retrieval passages)
  prompts/          instructions sent to the model
  evidence/         a saved log of every run
"""


def run_search(query: str, k: int) -> None:
    from .evidence import save_run
    from .retrieve import search
    hits, method = search(query, k)
    print(f"retrieval: {method}")
    if not hits:
        print(f'No passages match "{query}".')
    for h in hits:
        detail = f"bm25 #{h['bm25_rank']}" + (f", meaning #{h['dense_rank']}" if "dense_rank" in h else "")
        print(f"\n[{h['rank']}] {h['source']}   ({detail})")
        print(f"    section: {h['section']}  (lines {h['lines'][0]}-{h['lines'][1]})")
        print(textwrap.indent(h["text"], "    "))
    path = save_run("search", {"query": query, "k": k, "retrieval": method, "retrieved": hits})
    print(f"\nsaved: {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wiki", description=HELP,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["local", "online"], default="local",
                        help="where the model runs (default: local)")
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_ing = sub.add_parser("ingest", help="turn raw sources into wiki notes")
    p_ing.add_argument("path", type=Path, help="folder or file inside vault/raw, e.g. ./vault/raw")
    p_ing.add_argument("--force", action="store_true", help="regenerate even if the source is unchanged")
    p_ing.add_argument("--replan", action="store_true", help="ask Gemma to choose subjects again")
    p_ing.add_argument("--overwrite-edits", action="store_true", help="replace notes I edited by hand")

    sub.add_parser("chat", help="personal assistant with conversation context")

    p_ask = sub.add_parser("ask", help="grounded answer with citations (standalone)")
    p_ask.add_argument("question", help='e.g. "What learning rate did I use in Assignment 3?"')

    p_sea = sub.add_parser("search", help="show matching original passages (no model)")
    p_sea.add_argument("query", help='what to look for, e.g. "learning rate"')
    p_sea.add_argument("-k", type=int, default=5, help="number of passages (default 5)")

    p_ren = sub.add_parser("rename", help="rename a note, or merge it into an existing one")
    p_ren.add_argument("old", help="current note title")
    p_ren.add_argument("new", help="new title (an existing title merges the two notes)")
    p_ren.add_argument("--folder", choices=config.TOPIC_FOLDERS, help="also move it to this folder")
    p_ren.add_argument("--overwrite-edits", action="store_true", help="allow re-rendering a hand-edited note")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    if args.mode == "online":
        print("error: online mode is not configured. Local mode is the default: omit --mode.", file=sys.stderr)
        return 2

    model = "none (retrieval only)" if args.command in ("search", "rename") else config.MODEL
    print(f"wiki {args.command} · model {model} · mode {args.mode}")
    try:
        if args.command == "ingest":
            from .ingest import ingest
            ingest(args.path, force=args.force, replan=args.replan, overwrite_edits=args.overwrite_edits)
        elif args.command == "chat":
            from .chat import run
            run()
        elif args.command == "ask":
            from .ask import ask, show
            show(ask(args.question))
        elif args.command == "search":
            run_search(args.query, args.k)
        elif args.command == "rename":
            from .rename import rename
            rename(args.old, args.new, folder=args.folder, overwrite_edits=args.overwrite_edits)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except llm.ModelUnavailable as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
