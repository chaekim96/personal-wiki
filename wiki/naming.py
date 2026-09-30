"""Note-title rules. The model may propose a title; this code decides whether it is allowed.

A valid title is a short subject name (2-6 words) such as "GPU Parallel Training".
It becomes both the filename ("GPU Parallel Training.md") and the first heading.
"""
import re

SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "vs"}
QUESTION_STARTS = {"how", "what", "why", "when", "where", "who", "which", "is", "are", "does", "do", "can"}
BAD_CHARS = re.compile(r'[\\/:*?"<>|#^\[\]{}]')


def clean(title: str) -> str:
    """Tidy a proposed title: drop '.md', illegal filename characters, extra spaces; Title Case."""
    t = re.sub(r"\.md$", "", title.strip(), flags=re.I)
    t = BAD_CHARS.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip(" .-")
    words = []
    for i, w in enumerate(t.split(" ")):
        if w.isupper() or any(c.isupper() for c in w[1:]):   # keep acronyms/brands: RAG, nanoGPT, LLM
            words.append(w)
        elif i > 0 and w.lower() in SMALL_WORDS:
            words.append(w.lower())
        else:
            words.append(w[:1].upper() + w[1:])
    return " ".join(words)


def problems(title: str) -> list[str]:
    """Return the reasons a (cleaned) title is not allowed; empty list = OK."""
    issues = []
    n = len(title.split())
    if not 2 <= n <= 6:
        issues.append(f"must be 2-6 words (has {n})")
    if re.search(r"\b[0-9a-f]{6,}\b", title, re.I) and re.search(r"\d", title):
        issues.append("looks like a hash or ID")
    if re.search(r"\d{4}-\d{2}|\d{8}|T\d{6}", title):
        issues.append("contains a date or timestamp")
    if re.search(r"\b(chunk|passage|part|task|section|page)\s*\d+", title, re.I):
        issues.append("contains a chunk/task/section number")
    if re.search(r"[0-9a-f]{8}-[0-9a-f]{4}", title, re.I):
        issues.append("contains a UUID")
    if title.split(" ")[0].lower() in QUESTION_STARTS or title.endswith(("?", "!")):
        issues.append("reads like a question or sentence, not a subject name")
    return issues


def validate(proposed: str) -> tuple[str, list[str]]:
    """Clean a proposed title and check it. Returns (clean_title, problems)."""
    title = clean(proposed)
    return title, problems(title)


def key(title: str) -> str:
    """Comparison key so 'Transformer architecture' and 'Transformer Architecture' are the same note."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
