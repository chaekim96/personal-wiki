"""`wiki rename "Old" "New"`: rename a note, or merge it into an existing note.

No model call. Everything is driven by data/catalog.json:
  - the note entry moves to the new title (or its parts merge into the existing note)
  - every source's saved plan is updated, so re-ingest keeps the new name
  - related-note links pointing at the old title are redirected
  - the old file is deleted, all notes are re-rendered, and index.md is rebuilt
"""
from . import config, naming
from .ingest import build_index, find_note, load_catalog, note_path, save_catalog, sha1, write_note


def _edited(note: dict) -> bool:
    path = config.ROOT / note.get("path", "")
    return bool(note.get("path")) and path.exists() and sha1(path.read_text(encoding="utf-8")) != note.get("written_sha1")


def rename(old: str, new: str, folder: str | None = None, overwrite_edits: bool = False) -> None:
    cat = load_catalog()
    old_title = find_note(cat, old)
    if not old_title:
        raise FileNotFoundError(f'No note called "{old}". Notes: {", ".join(sorted(cat["notes"]))}')
    new_title, issues = naming.validate(new)
    if issues:
        raise ValueError(f'"{new_title}" is not a valid note title: {"; ".join(issues)}')
    if folder and folder not in config.TOPIC_FOLDERS:
        raise ValueError(f"folder must be one of {config.TOPIC_FOLDERS}")

    note = cat["notes"][old_title]
    if _edited(note) and not overwrite_edits:
        raise ValueError(f"{note['path']} has manual edits; renaming re-renders it from the catalog and would lose them.\n"
                         "Rename first, then edit - or pass --overwrite-edits.")
    old_path = config.ROOT / note["path"] if note.get("path") else None

    target = find_note(cat, new_title)
    if target and target != old_title:
        # MERGE: move each source part into the existing note
        into = cat["notes"][target]
        for sid, part in note["parts"].items():
            if sid in into["parts"]:
                mine = into["parts"][sid]
                mine["details"] += [d for d in part["details"] if d not in mine["details"]]
                mine["sections"] += [s for s in part["sections"] if s not in mine["sections"]]
                mine["summary"] = mine["summary"] + " " + part["summary"]
            else:
                into["parts"][sid] = part
        into["related"] += [r for r in note.get("related", [])
                            if r["title"] not in (target, old_title) and r["title"] not in {x["title"] for x in into["related"]}]
        into["related"] = into["related"][:3]
        if folder:
            into["folder"] = folder
        del cat["notes"][old_title]
        final = target
        print(f'merged "{old_title}" into "{target}"')
    else:
        # RENAME (a case-only change like "Rag" -> "RAG" also lands here)
        cat["notes"][new_title] = cat["notes"].pop(old_title)
        if folder:
            cat["notes"][new_title]["folder"] = folder
        final = new_title
        print(f'renamed "{old_title}" -> "{new_title}" ({cat["notes"][final]["folder"]})')

    # keep the source -> note mapping in sync, so the next ingest reuses the new name
    for src in cat["sources"].values():
        merged_plan: list[dict] = []
        for subj in src.get("plan", []):
            if subj["title"] == old_title:
                subj = {**subj, "title": final, "folder": cat["notes"][final]["folder"]}
            same = next((p for p in merged_plan if p["title"] == subj["title"]), None)
            if same:
                same["sections"] += [s for s in subj["sections"] if s not in same["sections"]]
            else:
                merged_plan.append(subj)
        src["plan"] = merged_plan
        src["notes"] = [p["title"] for p in merged_plan]

    # redirect related links; drop self-links created by a merge
    for title, n in cat["notes"].items():
        for r in n.get("related", []):
            if r["title"] == old_title:
                r["title"] = final
        n["related"] = [r for r in n.get("related", []) if r["title"] != title]

    # hand-edited notes are not re-rendered, so fix their [[links]] as text
    for title, n in cat["notes"].items():
        if title != final and _edited(n):
            path = config.ROOT / n["path"]
            text = path.read_text(encoding="utf-8")
            fixed = text.replace(f"[[{old_title}]]", f"[[{final}]]").replace(f"[[{old_title}|", f"[[{final}|")
            if fixed != text:
                path.write_text(fixed, encoding="utf-8")   # written_sha1 unchanged: still counts as edited
                print(f"  fixed links in your edited note {n['path']}")

    if old_path and old_path.exists() and old_path != note_path(final, cat["notes"][final]["folder"]):
        old_path.unlink()
    cat["notes"][final]["written_sha1"] = None           # force a fresh render of the renamed/merged note
    for title in sorted(cat["notes"]):
        write_note(title, cat, overwrite_edits=False)
    build_index(cat)
    save_catalog(cat)
    print(f"now: {cat['notes'][final]['path']} · index.md rebuilt")
