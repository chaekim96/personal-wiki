"""`wiki ask`: the RAG workflow. Standalone: no chat history, no persona.

question -> retrieve top passages -> label them P1..Pk -> build prompt from wiki-instructions.md
-> local Gemma returns JSON -> code checks every citation -> display + save evidence.
"""
import re
import time

from . import config, llm
from .evidence import save_run
from .retrieve import search

K = 5                       # passages sent to Gemma (~5 x 250 words = ~1,700 tokens)
INSUFFICIENT = "Insufficient evidence: the retrieved passages do not answer this question."


def load_instructions(name: str) -> str:
    """Return the part of prompts/<name> below the '---' line (the part meant for the model)."""
    text = (config.PROMPTS / name).read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1].strip()


def build_prompt(question: str, hits: list[dict]) -> list[dict]:
    blocks = [f"[P{i}] source: {h['source']} | section: {h['section']} | lines {h['lines'][0]}-{h['lines'][1]}\n{h['text']}"
              for i, h in enumerate(hits, 1)]
    user = "PASSAGES:\n\n" + "\n\n".join(blocks) + f"\n\nQUESTION: {question}"
    return [{"role": "system", "content": load_instructions("wiki-instructions.md")},
            {"role": "user", "content": user}]


def check_citations(answer: str, cited: list[str], labels: list[str], insufficient: bool) -> tuple[str, list[str]]:
    """The harness, not the model, decides whether the citations are acceptable.
    Returns (status, problems). status: 'answered' | 'insufficient' | 'failed-citation-check'."""
    problems = []
    inline = re.findall(r"\[(P\d+)\]", answer)
    for label in set(inline) | set(cited):
        if label not in labels:
            problems.append(f"{label} is not one of the retrieved passages ({', '.join(labels)})")
    if insufficient:
        return ("insufficient", problems) if not problems else ("failed-citation-check", problems)
    if not inline:
        problems.append("the answer states facts but has no inline [P#] citation")
    missing = set(inline) - set(cited)
    if missing:
        problems.append(f"cited inline but not listed: {', '.join(sorted(missing))}")
    return ("failed-citation-check" if problems else "answered"), problems


def ask(question: str) -> dict:
    llm.check_model()                      # clear error now, rather than after retrieval
    t0 = time.perf_counter()
    hits, method = search(question, K)
    t_retrieve = round(time.perf_counter() - t0, 2)
    if not hits:
        record = {"question": question, "retrieval": method, "retrieved": [], "status": "insufficient",
                  "answer": INSUFFICIENT + " (no passage matched)", "citations": []}
        record["saved"] = save_run("ask", record)
        return record

    labels = [f"P{i}" for i in range(1, len(hits) + 1)]
    # field order matters: the model writes the answer first, then judges whether it is supported
    schema = {"type": "object", "properties": {
        "answer": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string", "enum": labels}},
        "insufficient": {"type": "boolean"},
    }, "required": ["answer", "citations", "insufficient"]}
    messages = build_prompt(question, hits)
    data, info = llm.chat_json(messages, schema, temperature=0.0, num_predict=600)

    answer = data["answer"].strip()
    status, problems = check_citations(answer, data["citations"], labels, data["insufficient"])
    cited = sorted(set(re.findall(r"\[(P\d+)\]", answer)) | set(data["citations"]), key=lambda s: int(s[1:]))
    citations = [{"label": c, "source": hits[int(c[1:]) - 1]["source"], "section": hits[int(c[1:]) - 1]["section"],
                  "lines": hits[int(c[1:]) - 1]["lines"]} for c in cited if c in labels]

    record = {
        "question": question, "retrieval": method, "k": K,
        "retrieved": [{"label": l, **{f: h[f] for f in ("id", "source", "section", "lines", "rank", "bm25_rank", "text")},
                       "dense_rank": h.get("dense_rank")} for l, h in zip(labels, hits)],
        "model_output_raw": info["text"], "insufficient_flag": data["insufficient"],
        "answer": answer, "citations": citations, "status": status, "citation_problems": problems,
        "timing_s": {"retrieve": t_retrieve, "generate": info["seconds"], "total": round(time.perf_counter() - t0, 2)},
        "tokens": {"prompt": info["prompt_tokens"], "output": info["output_tokens"]},
        "instructions_file": "prompts/wiki-instructions.md", "chat_history_used": False, "persona_used": False,
    }
    record["saved"] = save_run("ask", record)
    return record


def show(record: dict) -> None:
    print(f"retrieval: {record['retrieval']} · {len(record['retrieved'])} passages")
    status = record["status"]
    print()
    if status == "insufficient":
        print(INSUFFICIENT)
        if record["answer"] and record["answer"] != INSUFFICIENT:
            print(f"Model's note: {record['answer']}")
    elif status == "failed-citation-check":
        print("!! CITATION CHECK FAILED - this answer is NOT verified evidence:")
        for p in record["citation_problems"]:
            print(f"   - {p}")
        print(f"\n(unverified) {record['answer']}")
    else:
        print(record["answer"])
    if record["citations"]:
        print("\nCitations:")
        for c in record["citations"]:
            print(f"  [{c['label']}] {c['source']} · {c['section']} · lines {c['lines'][0]}-{c['lines'][1]}")
    print("\nRetrieved passages:")
    for r in record["retrieved"]:
        print(f"  [{r['label']}] {r['source'].split('/')[-1]} · {r['section'].split(' > ')[-1]} · lines {r['lines'][0]}-{r['lines'][1]}")
    t = record.get("timing_s")
    if t:
        print(f"\ntime: retrieve {t['retrieve']} s · generate {t['generate']} s · total {t['total']} s")
    print(f"saved: {record['saved']}")
