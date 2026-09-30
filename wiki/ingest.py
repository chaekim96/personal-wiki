"""`wiki ingest`: raw source -> local Gemma -> reviewed-ready wiki notes + catalog + index.

Per source:
  1. PLAN  call: Gemma sees only the section list and proposes 1-3 subjects (title, folder, sections).
     Code validates titles. On re-ingest the saved plan is reused, so the same notes are updated.
  2. WRITE call per subject: Gemma sees the text of those sections (capped at MAX_WORDS_PER_CALL)
     and returns a summary + detail points, each tagged with the section it came from.
  3. Code renders the note file: frontmatter, summary, details, source references, related links.
After all sources:
  4. LINK call per changed note: Gemma picks related notes (only existing titles, with a reason).
  5. Code rebuilds vault/index.md and data/chunks.jsonl, and saves a run log in evidence/ingest/.
"""
import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path

from . import chunk, config, llm, naming

MAX_WORDS_PER_CALL = 1500   # source text sent to Gemma in one WRITE call (~2,000 tokens)

PLAN_SCHEMA = {
    "type": "object",
    "properties": {"subjects": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "folder": {"type": "string", "enum": config.TOPIC_FOLDERS},
            "sections": {"type": "array", "items": {"type": "integer"}},
        },
        "required": ["title", "folder", "sections"],
    }}},
    "required": ["subjects"],
}
WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "details": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "section": {"type": "string"}},
            "required": ["text", "section"],
        }},
    },
    "required": ["summary", "details"],
}
LINK_SCHEMA = {
    "type": "object",
    "properties": {"related": {"type": "array", "items": {
        "type": "object",
        "properties": {"title": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["title", "reason"],
    }}},
    "required": ["related"],
}


# ---------- small helpers ----------

def load_prompts() -> dict[str, str]:
    """Split prompts/ingest-instructions.md into {'plan': ..., 'write': ..., 'link': ...}."""
    text = (config.PROMPTS / "ingest-instructions.md").read_text(encoding="utf-8")
    parts = re.split(r"^## (\w+)\s*$", text, flags=re.M)
    return {parts[i].lower(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def load_catalog() -> dict:
    if config.CATALOG.exists():
        return json.loads(config.CATALOG.read_text(encoding="utf-8"))
    return {"sources": {}, "notes": {}}


def save_catalog(cat: dict) -> None:
    config.DATA.mkdir(exist_ok=True)
    config.CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False), encoding="utf-8")


def sha1(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]


def find_note(cat: dict, title: str) -> str | None:
    """Existing note title with the same comparison key, if any."""
    k = naming.key(title)
    return next((t for t in cat["notes"] if naming.key(t) == k), None)


def section_list(passages: list[dict]) -> list[dict]:
    """Ordered unique sections of one source with word counts and line ranges."""
    out: dict[str, dict] = {}
    for p in passages:
        s = out.setdefault(p["section"], {"name": p["section"], "words": 0, "lines": p["lines"][:]})
        s["words"] += p["words"]
        s["lines"][1] = max(s["lines"][1], p["lines"][1])
    return list(out.values())


# ---------- the three kinds of model call ----------

def plan_subjects(prompts, meta, sections, cat, log) -> list[dict]:
    existing = "\n".join(f"- {t} ({n['folder']})" for t, n in cat["notes"].items()) or "(none yet)"
    system = prompts["plan"].replace("<EXISTING_NOTES>", existing)
    listing = "\n".join(f"{i}. {s['name']} ({s['words']} words)" for i, s in enumerate(sections, 1))
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": f"SOURCE: {meta['title']}\n\nSECTIONS:\n{listing}"}]

    for attempt in (1, 2):
        data, info = llm.chat_json(messages, PLAN_SCHEMA, num_predict=512)
        log.append({"call": "plan", "attempt": attempt, **info})
        subjects, rejected = [], []
        for s in data["subjects"][:3]:
            title, issues = naming.validate(s["title"])
            secs = [sections[i - 1]["name"] for i in s["sections"] if 1 <= i <= len(sections)]
            if issues:
                rejected.append(f'"{s["title"]}": {"; ".join(issues)}')
            elif not secs:
                rejected.append(f'"{s["title"]}": no valid section numbers')
            else:
                same = find_note(cat, title) or next((x["title"] for x in subjects
                                                      if naming.key(x["title"]) == naming.key(title)), None)
                if same and any(x["title"] == same for x in subjects):   # duplicate inside this plan: merge
                    dup = next(x for x in subjects if x["title"] == same)
                    dup["sections"] += [x for x in secs if x not in dup["sections"]]
                else:
                    folder = cat["notes"][same]["folder"] if same in cat["notes"] else s["folder"]
                    subjects.append({"title": same or title, "folder": folder, "sections": secs})
        if not rejected or attempt == 2:
            for r in rejected:
                print(f"    ! dropped proposed title {r}")
            return subjects
        # one retry: tell the model exactly what the code rejected
        messages += [{"role": "assistant", "content": info["text"]},
                     {"role": "user", "content": "These titles were rejected by the naming rules:\n"
                      + "\n".join(rejected) + "\nReturn the full subject list again with fixed titles."}]
    return []


def write_part(prompts, title, section_names, passages, log) -> dict:
    """WRITE call: send the chosen sections (capped) and get summary + details back."""
    labels, blocks, words, truncated = {}, [], 0, False
    for p in passages:
        if p["section"] not in section_names:
            continue
        if words + p["words"] > MAX_WORDS_PER_CALL:
            truncated = True
            break
        if p["section"] not in labels:
            labels[p["section"]] = f"S{len(labels) + 1}"
            blocks.append(f"\n[{labels[p['section']]}] {p['section']}")
        blocks.append(p["text"])
        words += p["words"]
    by_label = {v: k for k, v in labels.items()}

    # restrict "section" to the labels we actually sent, so Ollama cannot return anything else
    schema = json.loads(json.dumps(WRITE_SCHEMA))
    schema["properties"]["details"]["items"]["properties"]["section"]["enum"] = list(by_label)
    messages = [{"role": "system", "content": prompts["write"].replace("<TITLE>", title)},
                {"role": "user", "content": f"SUBJECT: {title}\n\nSOURCE TEXT:" + "\n".join(blocks)}]
    data, info = llm.chat_json(messages, schema, num_predict=1024)
    log.append({"call": "write", "title": title, "words_sent": words, "truncated": truncated, **info})

    details, dropped = [], 0
    for d in data["details"]:
        label, text = d["section"].strip().strip("[]"), d["text"].strip()
        # a detail must be traceable (valid label) and an actual statement, not just "S1"
        if label in by_label and len(text.split()) >= 5 and not re.fullmatch(r"\[?S\d+\]?", text):
            details.append({"text": text, "section": by_label[label]})
        else:
            dropped += 1
    if dropped:
        print(f"    ! dropped {dropped} detail(s): missing section label or not a real statement")
    return {"summary": data["summary"].strip(), "details": details,
            "sections": list(labels), "words_sent": words, "truncated": truncated}


def link_note(prompts, title, cat, log) -> list[dict]:
    """LINK call: choose up to 3 related existing notes, each with a reason."""
    others = [t for t in cat["notes"] if t != title]
    if not others:
        return []
    note = cat["notes"][title]
    summary = " ".join(p["summary"] for p in note["parts"].values())
    listing = "\n".join(
        f"- {t}: {first_sentence(next(iter(cat['notes'][t]['parts'].values()))['summary'])}" for t in others)
    messages = [{"role": "system", "content": prompts["link"]},
                {"role": "user", "content": f"NOTE: {title}\n{summary}\n\nOTHER NOTES:\n{listing}"}]
    data, info = llm.chat_json(messages, LINK_SCHEMA, num_predict=400)
    log.append({"call": "link", "title": title, **info})
    related, seen = [], set()
    for r in data["related"]:
        match = find_note(cat, r["title"])
        if match and match != title and match not in seen and r["reason"].strip():
            related.append({"title": match, "reason": r["reason"].strip()})
            seen.add(match)
    return related[:3]


# ---------- rendering ----------

def note_path(title: str, folder: str) -> Path:
    return config.WIKI / folder / f"{title}.md"


def render_note(title: str, cat: dict) -> str:
    note = cat["notes"][title]
    srcs = [(sid, cat["sources"][sid]) for sid in note["parts"]]
    today = dt.date.today().isoformat()
    fm = ["---", f"title: {title}", f"folder: {note['folder']}",
          "source_ids: [" + ", ".join(sid for sid, _ in srcs) + "]",
          "original_files: [" + ", ".join(json.dumps(s["original_filename"]) for _, s in srcs) + "]",
          f"generated_by: {config.MODEL} (local)", f"updated: {today}", "---", ""]
    body = [f"# {title}", "", "## Summary", ""]
    for sid, src in srcs:
        part = note["parts"][sid]
        prefix = f"**From {src['label']}:** " if len(srcs) > 1 else ""
        body += [prefix + part["summary"], ""]
    body += ["## Details", ""]
    for sid, src in srcs:
        for d in note["parts"][sid]["details"]:
            short = d["section"].split(" > ")[-1]
            body.append(f"- {d['text']} *({src['label']}, {short})*")
    body += ["", "## Sources", ""]
    for sid, src in srcs:
        part = note["parts"][sid]
        link = f"[[{Path(src['file']).stem}|{src['label']}]]"
        extra = f" · [Wikipedia permalink]({src['meta']['permalink']}) · {src['meta'].get('license', '').split(' (')[0]}" \
            if src["meta"].get("permalink") else ""
        body.append(f"- {link}{extra}")
        for name in part["sections"]:
            lines = src["sections"].get(name, ["?", "?"])
            body.append(f"  - {name} (lines {lines[0]}-{lines[1]})")
    related = [r for r in note.get("related", []) if r["title"] in cat["notes"]]
    body += ["", "## Related notes", ""]
    body += [f"- [[{r['title']}]] - {r['reason']}" for r in related] or ["- (none yet)"]
    return "\n".join(fm + body) + "\n"


def write_note(title: str, cat: dict, overwrite_edits: bool) -> str:
    """Write the note file unless the user edited it since our last write. Returns a status word."""
    note = cat["notes"][title]
    path = note_path(title, note["folder"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and note.get("written_sha1") and sha1(path.read_text(encoding="utf-8")) != note["written_sha1"] \
            and not overwrite_edits:
        print(f"    ! kept your manual edits in {path.relative_to(config.ROOT)} (use --overwrite-edits to replace)")
        return "kept-edits"
    text = render_note(title, cat)
    status = "updated" if path.exists() else "created"
    path.write_text(text, encoding="utf-8")
    note["written_sha1"] = sha1(text)
    note["path"] = path.relative_to(config.ROOT).as_posix()
    return status


def note_summary(title: str, cat: dict) -> str:
    """The summary a reader sees: taken from the note file itself (so hand edits count),
    falling back to the catalog if the file has no Summary section."""
    note = cat["notes"][title]
    path = config.ROOT / note.get("path", "")
    if note.get("path") and path.exists():
        m = re.search(r"^## Summary\s*\n+(.+?)(?:\n\n|\n## )", path.read_text(encoding="utf-8"), re.S | re.M)
        if m:
            return re.sub(r"^\*\*From [^*]+:\*\* ", "", m.group(1).strip())
    return next(iter(note["parts"].values()))["summary"]


def build_index(cat: dict) -> None:
    lines = ["# Index", "",
             "Personal study wiki for MBA 290T. Notes are generated by local Gemma from the files in `raw/`,",
             "then reviewed by me. Each note lists its sources.", ""]
    descriptions = {"Concepts": "Ideas and techniques explained by my sources.",
                    "Projects": "Things I built or ran."}
    for folder in config.TOPIC_FOLDERS:
        titles = sorted(t for t, n in cat["notes"].items() if n["folder"] == folder)
        if not titles:
            continue
        lines += [f"## {folder}", "", descriptions.get(folder, ""), ""]
        for t in titles:
            lines.append(f"- [[{t}]] - {first_sentence(note_summary(t, cat))}")
        lines.append("")
    lines += ["## Sources", ""]
    for sid, s in sorted(cat["sources"].items(), key=lambda kv: kv[1]["label"]):
        notes = ", ".join(f"[[{t}]]" for t in s["notes"])
        lines.append(f"- [[{Path(s['file']).stem}|{s['label']}]] -> {notes}")
    config.INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- the command ----------

def ingest(folder: Path, force: bool = False, replan: bool = False, overwrite_edits: bool = False) -> dict:
    folder = folder.resolve()
    if not folder.exists():
        raise FileNotFoundError(f"No such folder: {folder}")
    try:
        folder.relative_to(config.RAW.resolve())
    except ValueError:
        raise FileNotFoundError(f"Sources must be inside {config.RAW.relative_to(config.ROOT)}/ (got {folder})")
    files = chunk.raw_files(folder) if folder.is_dir() else [folder]
    if not files:
        raise FileNotFoundError(f"No .md or .txt files in {folder}")

    llm.check_model()
    llm.check_model(config.EMBED_MODEL)
    prompts, cat = load_prompts(), load_catalog()
    run = {"command": "ingest", "mode": "local", "model": config.MODEL, "num_ctx": config.NUM_CTX,
           "started": dt.datetime.now().isoformat(timespec="seconds"), "sources": []}
    t0 = time.perf_counter()
    touched, new_notes = set(), False

    for path in files:
        sid = chunk.source_id(path)
        meta, passages = chunk.chunk_file(path)
        text_hash = sha1(path.read_text(encoding="utf-8"))
        src = cat["sources"].get(sid)
        rel = chunk.rel_path(path)
        print(f"\n{rel}  [{sid}]")
        entry = {"file": rel, "source_id": sid, "calls": []}
        run["sources"].append(entry)

        if src and src["sha1"] == text_hash and not force and not replan:
            print("  unchanged since last ingest - skipped (use --force to regenerate)")
            entry["status"] = "skipped-unchanged"
            continue

        sections = section_list(passages)
        cat["sources"][sid] = src = {
            **(src or {}), "file": rel, "original_filename": path.name, "sha1": text_hash,
            "label": meta["title"], "meta": meta,
            "sections": {s["name"]: s["lines"] for s in sections},
            "ingested": dt.datetime.now().isoformat(timespec="seconds"),
        }

        if src.get("plan") and not replan:
            plan = src["plan"]                              # stable mapping: same subjects as last time
            print(f"  re-using saved plan: {', '.join(p['title'] for p in plan)}")
        else:
            plan = plan_subjects(prompts, meta, sections, cat, entry["calls"])
            print(f"  planned: {', '.join(p['title'] + ' (' + p['folder'] + ')' for p in plan)}")
            for old in set(src.get("notes", [])) - {p["title"] for p in plan}:  # replan dropped a note
                cat["notes"].get(old, {}).get("parts", {}).pop(sid, None)
        src["plan"], src["notes"] = plan, [p["title"] for p in plan]

        for subj in plan:
            part = write_part(prompts, subj["title"], subj["sections"], passages, entry["calls"])
            call = entry["calls"][-1]
            note = cat["notes"].get(subj["title"])
            if note is None:
                note = cat["notes"][subj["title"]] = {"folder": subj["folder"], "parts": {}, "related": []}
                new_notes = True
            note["parts"][sid] = part
            touched.add(subj["title"])
            print(f"  wrote {subj['title']}: sent {part['words_sent']} words"
                  f"{' (truncated)' if part['truncated'] else ''}, {len(part['details'])} details, {call['seconds']} s")
        entry["status"] = "ingested"

    # notes left with no source parts (after --replan) are removed from the catalog
    for title in [t for t, n in cat["notes"].items() if not n["parts"]]:
        note = cat["notes"].pop(title)
        touched.discard(title)
        path = config.ROOT / note.get("path", "")
        if note.get("path") and path.exists():
            if sha1(path.read_text(encoding="utf-8")) == note.get("written_sha1") or overwrite_edits:
                path.unlink()
                print(f"  removed note no longer planned: {note['path']}")
            else:
                print(f"  ! {note['path']} is no longer planned but has your edits - left in place")

    if touched:
        to_link = set(cat["notes"]) if new_notes else touched
        print(f"\nlinking {len(to_link)} note(s)")
        link_log = []
        run["link_calls"] = link_log
        for title in sorted(to_link):
            cat["notes"][title]["related"] = link_note(prompts, title, cat, link_log)
        for title in sorted(cat["notes"]):
            status = write_note(title, cat, overwrite_edits)
            print(f"  {status}: {cat['notes'][title]['path'] if 'path' in cat['notes'][title] else title}")

    build_index(cat)
    save_catalog(cat)
    passages = chunk.write_chunks()
    n_passages = len(passages)
    from .retrieve import build_embeddings
    new_vectors = build_embeddings(passages)
    run["embeddings_new"] = new_vectors
    run["seconds_total"] = round(time.perf_counter() - t0, 2)
    run["notes"] = sorted(cat["notes"])
    run["passages_indexed"] = n_passages

    log_dir = config.EVIDENCE / "ingest"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"ingest_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nindex.md rebuilt · {n_passages} passages indexed ({new_vectors} newly embedded) · {run['seconds_total']} s total")
    print(f"run log: {log_path.relative_to(config.ROOT)}")
    return run
