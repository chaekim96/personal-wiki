"""`wiki chat`: personal assistant (persona.md) with recent conversation context.

Each turn:
  1. ROUTE: decide whether this turn needs the notes.
     Code rules first (greetings, "what can you do", "make that shorter" -> no search),
     otherwise a small Gemma call (prompts/chat-router.md) returns needs_notes + search_query.
  2. RETRIEVE only if needed: top passages, labeled N1..N4, added for THIS turn only.
  3. REPLY: persona + last HISTORY_TURNS turns + (notes) + the new message -> Gemma (plain text).
  4. CHECK: every [N#] in the reply must be a passage given this turn.
  5. SAVE the turn to evidence/runs/ and keep the reply in the conversation history.
Chat history is conversation context only. It is never used as evidence by `wiki ask`.
"""
import datetime as dt
import re
import time

from . import config, llm
from .ask import load_instructions
from .evidence import save_run
from .ingest import load_catalog
from .retrieve import search

HISTORY_TURNS = 6          # user+assistant pairs kept as context
K = 4                      # passages when a turn needs the notes
CAPABILITY_REASON = "question about the assistant's own capabilities"
CAPABILITY_HINT = ("The student is asking what you can do. Answer from your 'What you can actually do' list: "
                   "include looking things up in their wiki with citations (name the sources), follow-ups on this "
                   "conversation, and the wiki ask/search commands. Also say briefly what you cannot do. "
                   "Do not offer anything outside that list. End with one suggested starting point.")
NO_NOTES_RULES = [         # (pattern, reason) - checked before calling the router
    (r"^(hi|hello|hey|thanks|thank you|ok|okay|cool|bye)\b", "greeting or small talk"),
    (r"\b(what can (you|we|i) do|what can you help|help me with\?|who are you|what are you|your capabilities)\b",
     CAPABILITY_REASON),
    (r"\b(shorter|longer|shorten|rephrase|rewrite|reword|simpler|more formal|less formal|bullet|as a list)\b.*\b(that|it|this)\b"
     r"|\b(make|turn) (that|it|this)\b",
     "follow-up that rewrites the previous reply"),
]
ROUTER_SCHEMA = {"type": "object", "properties": {
    "needs_notes": {"type": "boolean"}, "search_query": {"type": "string"}, "reason": {"type": "string"}},
    "required": ["needs_notes", "search_query", "reason"]}


def sources_list() -> str:
    cat = load_catalog()
    return "\n".join(f"  - {s['label']} -> notes: {', '.join(s['notes'])}" for s in cat["sources"].values()) \
        or "  - (no sources ingested yet)"


class ChatSession:
    def __init__(self):
        self.history: list[dict] = []          # [{"role": "user"|"assistant", "content": ...}]
        self.session = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.turn_no = 0
        srcs = sources_list()
        self.persona = load_instructions("persona.md").replace("<SOURCES>", srcs)
        self.router = load_instructions("chat-router.md").replace("<SOURCES>", srcs.replace("\n", " "))

    def route(self, message: str) -> dict:
        text = message.lower().strip()
        for pattern, reason in NO_NOTES_RULES:
            if re.search(pattern, text):
                return {"needs_notes": False, "search_query": "", "reason": reason, "decided_by": "code rule"}
        recent = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in self.history[-4:]) or "(start of conversation)"
        data, info = llm.chat_json(
            [{"role": "system", "content": self.router},
             {"role": "user", "content": f"RECENT CONVERSATION:\n{recent}\n\nNEW MESSAGE: {message}"}],
            ROUTER_SCHEMA, temperature=0.0, num_predict=120)
        return {**data, "decided_by": "router model", "router_seconds": info["seconds"]}

    def turn(self, message: str) -> dict:
        self.turn_no += 1
        t0 = time.perf_counter()
        decision = self.route(message)

        hits, method, notes_msg = [], None, []
        if decision["needs_notes"]:
            hits, method = search(decision["search_query"] or message, K)
            blocks = [f"[N{i}] {h['source'].split('/')[-1]} | {h['section']}\n{h['text']}" for i, h in enumerate(hits, 1)]
            notes_msg = [{"role": "system", "content": "NOTES for this turn. Cite every fact you take from them with its label, "
                          "like [N1], even inside a draft:\n\n" + "\n\n".join(blocks)}]

        # the harness knows this is a capability question, so it asks for the full, accurate list
        hint = [{"role": "system", "content": CAPABILITY_HINT}] if decision["reason"] == CAPABILITY_REASON else []
        messages = ([{"role": "system", "content": self.persona}] + self.history[-2 * HISTORY_TURNS:]
                    + notes_msg + hint + [{"role": "user", "content": message}])
        info = llm.chat(messages, temperature=0.6, num_predict=700)
        reply = info["text"].strip()
        labels = {f"N{i}": h for i, h in enumerate(hits, 1)}
        retried = False
        if hits and not re.search(r"\[N\d+\]", reply):
            # one repair attempt: tell the model exactly what the harness found
            retried = True
            info = llm.chat(messages + [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": "Rewrite that reply with the same content, adding the [N#] label after "
                 "every fact taken from the NOTES. Remove any statement about my work that the NOTES do not support."}],
                temperature=0.3, num_predict=700)
            reply = info["text"].strip()

        used = sorted(set(re.findall(r"\[(N\d+)\]", reply)), key=lambda s: int(s[1:]))
        bad = [f"{u} was not provided this turn" for u in used if u not in labels]
        if hits and not used:
            bad.append("notes were provided but the reply cites none of them (claims from notes are uncited)")
        citations = [{"label": u, "source": labels[u]["source"], "section": labels[u]["section"],
                      "lines": labels[u]["lines"]} for u in used if u in labels]

        # keep history readable for later turns: replace this turn's [N#] labels with source names
        stored = re.sub(r"\[(N\d+)\]", lambda m: f"[{labels[m.group(1)]['source'].split('/')[-1][:-3]}, "
                        f"{labels[m.group(1)]['section'].split(' > ')[-1]}]" if m.group(1) in labels else m.group(0), reply)
        self.history += [{"role": "user", "content": message}, {"role": "assistant", "content": stored}]

        record = {
            "session": self.session, "turn": self.turn_no, "message": message,
            "routing": decision, "retrieval": method,
            "retrieved": [{"label": f"N{i}", **{f: h[f] for f in ("id", "source", "section", "lines", "text")}}
                          for i, h in enumerate(hits, 1)],
            "history_messages_used": len(messages) - 2 - len(notes_msg) - len(hint),
            "reply": reply, "citation_retry": retried, "citations": citations, "citation_problems": bad,
            "instructions_file": "prompts/persona.md", "seconds": round(time.perf_counter() - t0, 2),
            "tokens": {"prompt": info["prompt_tokens"], "output": info["output_tokens"]},
        }
        record["saved"] = save_run("chat", record)
        return record


def show(record: dict) -> None:
    r = record["routing"]
    lookup = f"searched notes for \"{r['search_query']}\"" if r["needs_notes"] else "no notes search"
    print(f"\nwren> {record['reply']}")
    for c in record["citations"]:
        print(f"      [{c['label']}] {c['source']} · {c['section'].split(' > ')[-1]} · lines {c['lines'][0]}-{c['lines'][1]}")
    for p in record["citation_problems"]:
        print(f"      !! citation check: {p}")
    print(f"      ({lookup} - {r['reason']} [{r['decided_by']}] · {record['seconds']} s · saved {record['saved']})")


def run() -> None:
    llm.check_model()
    session = ChatSession()
    print("Wren (study partner) · type /help for what I can do, /exit to quit\n")
    while True:
        try:
            message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not message:
            continue
        if message in ("/exit", "/quit"):
            break
        if message == "/help":
            print("Commands: /exit to quit. Ask me anything; I search your notes only when a question needs them.\n"
                  "For strict answers with checked citations use: wiki ask \"...\"")
            continue
        try:
            show(session.turn(message))
        except llm.ModelUnavailable as e:
            print(f"error: {e}")
        print()
    print(f"session {session.session}: {session.turn_no} turn(s) saved in {config.EVIDENCE.relative_to(config.ROOT)}/runs/")
