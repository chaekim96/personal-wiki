"""Split raw sources into retrieval passages that keep their source path and section.

Two input styles are supported (.md or .txt files):
  Markdown  -> headings (#, ##, ...), paragraphs separated by blank lines
  Wikipedia -> plain-text extracts with a metadata header (Title:, Source: ...wikipedia.org...)
               at the top, headings like "== History ==", one paragraph per line

Wikipedia extracts also contain broken math: many indented MathML lines followed by an
indented "{\\displaystyle ...}" line. We keep the LaTeX as inline $...$ and drop the rest.
"""
import hashlib
import json
import re
from pathlib import Path

from . import config

MD_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
WIKI_HEADING = re.compile(r"^(={2,5})\s*(.*?)\s*\1\s*$")
DISPLAY_MATH = re.compile(r"^\s+\{\\displaystyle (.*)\}\s*$")
META_KEYS = ("Title", "Source", "Revision", "Permalink", "Retrieved", "License")
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def source_id(path: Path) -> str:
    """Stable machine ID from the file's path inside vault/raw (not its content),
    so re-ingesting an edited copy of the same file maps to the same notes."""
    rel = path.resolve().relative_to(config.RAW.resolve()).as_posix()
    return "src_" + hashlib.sha1(rel.encode()).hexdigest()[:10]


def rel_path(path: Path) -> str:
    """Path relative to the project root, e.g. 'vault/raw/Foo.md' (used in citations)."""
    return path.resolve().relative_to(config.ROOT).as_posix()


def read_metadata(lines: list[str]) -> tuple[dict, int]:
    """Read the 'Key: value' header of a Wikipedia extract. Returns (metadata, first body line)."""
    meta, i = {}, 0
    while i < len(lines) and ":" in lines[i] and lines[i].split(":", 1)[0] in META_KEYS:
        key, value = lines[i].split(":", 1)
        meta[key.lower()] = value.strip()
        i += 1
    return meta, i


def parse_sections(path: Path) -> tuple[dict, list[dict]]:
    """Return (metadata, sections). Each section: {section, paragraphs: [(line_no, text)]}."""
    lines = path.read_text(encoding="utf-8").splitlines()
    meta, start = read_metadata(lines)
    # Wikipedia extracts are recognised by their header, not by file extension
    is_md = "wikipedia.org" not in meta.get("source", "")
    if is_md:
        meta, start = {}, 0
    doc_title = meta.get("title") or path.stem

    sections: list[dict] = []
    stack: list[tuple[int, str]] = []          # (level, heading) for "A > B" section paths
    current = {"section": "Introduction" if not is_md else doc_title, "paragraphs": []}
    para: list[str] = []
    para_line = 0
    glue = False                               # True right after a formula: next line continues the sentence

    def flush():
        nonlocal para, glue
        text = ("\n" if is_md else "").join(para).strip()
        if text:
            current["paragraphs"].append((para_line, text))
        para, glue = [], False

    for no, line in enumerate(lines[start:], start=start + 1):
        heading = (MD_HEADING if is_md else WIKI_HEADING).match(line)
        if heading:
            flush()
            if current["paragraphs"]:
                sections.append(current)
            level, title = len(heading.group(1)), heading.group(2)
            stack = [(lv, t) for lv, t in stack if lv < level] + [(level, title)]
            current = {"section": " > ".join(t for _, t in stack), "paragraphs": []}
            continue

        if not is_md:
            math = DISPLAY_MATH.match(line)
            if math:                           # keep the formula inline, then keep gluing
                if not para:
                    para_line = no
                para.append(f" ${math.group(1)}$")
                glue = True
                continue
            if line.strip() == "" and line != "":
                continue                       # whitespace-only line inside a math block
            if line[:1] in (" ", "\t"):
                continue                       # indented MathML noise
            if line == "":
                flush()
                continue
            if glue:                           # sentence continues after a formula
                para.append(line if line[:1] in ",.;:)" else " " + line)
                continue
            flush()                            # in Wikipedia extracts, one line = one paragraph
            para_line = no
            para.append(line)
            continue

        # Markdown: paragraphs are separated by blank lines
        if line.strip() == "":
            flush()
        else:
            if not para:
                para_line = no
            para.append(line)

    flush()
    if current["paragraphs"]:
        sections.append(current)
    meta.setdefault("title", doc_title)
    return meta, sections


def split_long(text: str, limit: int) -> list[str]:
    """Split one very long paragraph at sentence ends into pieces of about `limit` words."""
    pieces, buf = [], []
    for sentence in SENTENCE_END.split(text):
        buf.append(sentence)
        if len(" ".join(buf).split()) >= limit:
            pieces.append(" ".join(buf))
            buf = []
    if buf:
        pieces.append(" ".join(buf))
    return pieces


def chunk_file(path: Path) -> tuple[dict, list[dict]]:
    """Return (metadata, passages) for one raw source."""
    sid = source_id(path)
    meta, sections = parse_sections(path)
    passages = []
    for sec in sections:
        if sec["section"].split(" > ")[0] in config.SKIP_SECTIONS:
            continue
        buf, buf_start, buf_end = [], 0, 0
        units = []                             # (line_no, text) with long paragraphs pre-split
        for line_no, text in sec["paragraphs"]:
            if len(text.split()) > config.PASSAGE_WORDS * 1.6:
                units += [(line_no, piece) for piece in split_long(text, config.PASSAGE_WORDS)]
            else:
                units.append((line_no, text))

        def emit():
            if buf:
                passages.append({
                    "id": f"{sid}:{len(passages):03d}",
                    "source_id": sid,
                    "source": rel_path(path),
                    "section": sec["section"],
                    "lines": [buf_start, buf_end],
                    "words": len(" ".join(buf).split()),
                    "text": "\n\n".join(buf),
                })

        for line_no, text in units:
            n = len(text.split())
            size = len(" ".join(buf).split())
            # start a new passage when this one is full, but never leave a tiny fragment
            # (e.g. a lone "Files: ..." line) as its own passage
            if buf and size + n > config.PASSAGE_WORDS and size >= config.MIN_PASSAGE_WORDS:
                emit()
                buf = []
            if not buf:
                buf_start = line_no
            buf.append(text)
            buf_end = line_no
        emit()
    return meta, passages


def raw_files(folder: Path) -> list[Path]:
    """All supported source files in a folder (sorted, so runs are repeatable)."""
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in (".md", ".txt") and p.is_file())


def write_chunks(folder: Path = config.RAW) -> list[dict]:
    """Chunk every raw source and rewrite data/chunks.jsonl. Returns all passages."""
    config.DATA.mkdir(exist_ok=True)
    all_passages = []
    for path in raw_files(folder):
        _, passages = chunk_file(path)
        all_passages += passages
    with open(config.CHUNKS, "w", encoding="utf-8") as f:
        for p in all_passages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return all_passages


if __name__ == "__main__":
    # Quick inspection: python -m wiki.chunk
    passages = write_chunks()
    by_source: dict[str, list[dict]] = {}
    for p in passages:
        by_source.setdefault(p["source"], []).append(p)
    for src, ps in by_source.items():
        words = [p["words"] for p in ps]
        print(f"{src}\n  passages: {len(ps)}  words: total {sum(words)}, "
              f"min {min(words)}, max {max(words)}, avg {sum(words) // len(words)}")
    print(f"\nwrote {len(passages)} passages to {config.CHUNKS.relative_to(config.ROOT)}")
