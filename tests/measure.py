"""Measure peak memory and wall time of one `wiki` command on macOS.

Usage: .venv/bin/python tests/measure.py <label> [--cold] -- wiki <args...>

- --cold: unload both models first (`ollama stop`), so model loading is included.
- Samples the physical footprint (what Activity Monitor shows; includes GPU/Metal memory on
  Apple Silicon) of every Ollama process (`ollama serve` + one `llama-server` per loaded model)
  about twice a second with `top`, and records the peak per process and the peak of their sum.
- The wiki CLI process itself is measured with `/usr/bin/time -l` (max resident set size).
- Also records `ollama ps` and system-wide free memory before/after.
Writes evidence/measurements/<label>.json and prints a summary.
"""
import json
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLLAMA = "/Applications/Ollama.app/Contents/Resources/ollama"
MODELS = ["gemma4:e2b-it-qat", "embeddinggemma:latest"]


def ollama_pids() -> dict[int, str]:
    out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout
    pids = {}
    for line in out.splitlines():
        pid, cmd = line.strip().split(" ", 1)
        if "llama-server" in cmd:
            m = re.search(r"--model \S+?sha256-([0-9a-f]{12})", cmd)
            pids[int(pid)] = "llama-server " + ("--embedding " if "--embedding" in cmd else "") + (m.group(1) if m else "")
        elif cmd.endswith("ollama serve"):
            pids[int(pid)] = "ollama serve"
    return pids


def footprint_mb(pids: list[int]) -> dict[int, float]:
    """Physical footprint per pid in MB, from one `top` sample."""
    if not pids:
        return {}
    args = ["top", "-l", "1", "-stats", "pid,mem"] + sum((["-pid", str(p)] for p in pids), [])
    out = subprocess.run(args, capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        m = re.match(r"^\s*(\d+)\s+([\d.]+)([BKMG])\+?-?\s*$", line)
        if m and int(m.group(1)) in pids:
            res[int(m.group(1))] = float(m.group(2)) * {"B": 1 / 2**20, "K": 1 / 1024, "M": 1, "G": 1024}[m.group(3)]
    return res


def free_percent() -> str:
    out = subprocess.run(["memory_pressure"], capture_output=True, text=True).stdout
    return out.strip().splitlines()[-1]


def main():
    label = sys.argv[1]
    cold = "--cold" in sys.argv
    cmd = sys.argv[sys.argv.index("--") + 1:]
    cmd[0] = str(ROOT / ".venv/bin" / cmd[0]) if cmd[0] == "wiki" else cmd[0]
    if cold:
        for m in MODELS:
            subprocess.run([OLLAMA, "stop", m], capture_output=True)
        time.sleep(2)

    before = {"free": free_percent(), "ollama_ps": subprocess.run([OLLAMA, "ps"], capture_output=True, text=True).stdout}
    samples, stop = [], threading.Event()

    def sampler():
        # streaming top: one sample per second of every process's physical footprint (MEM)
        top = subprocess.Popen(["top", "-l", "0", "-s", "1", "-stats", "pid,command,mem"],
                               stdout=subprocess.PIPE, text=True)
        block: dict[str, float] = {}
        for line in top.stdout:
            if line.startswith("Processes:"):
                if block:
                    samples.append({"t": round(time.perf_counter() - t0, 2), "per_process_mb": dict(block),
                                    "total_mb": round(sum(block.values()), 1)})
                block = {}
                if stop.is_set():
                    break
                continue
            m = re.match(r"^\s*(\d+)\s+(llama-server|ollama)\S*\s+([\d.]+)([BKMG])", line)
            if m:
                mb = float(m.group(3)) * {"B": 1 / 2**20, "K": 1 / 1024, "M": 1, "G": 1024}[m.group(4)]
                block[names.get(int(m.group(1)), m.group(2)) + f" [{m.group(1)}]"] = round(mb, 1)
        top.terminate()

    names: dict[int, str] = {}

    def refresh_names():
        while not stop.is_set():
            names.update(ollama_pids())
            time.sleep(0.5)

    t0 = time.perf_counter()
    th = threading.Thread(target=sampler, daemon=True)
    th2 = threading.Thread(target=refresh_names, daemon=True)
    th.start(); th2.start()
    proc = subprocess.run(["/usr/bin/time", "-l"] + cmd, capture_output=True, text=True, cwd=ROOT)
    wall = round(time.perf_counter() - t0, 2)
    time.sleep(1.5)
    stop.set()
    th.join(timeout=5)
    # end-of-run breakdown: footprint vs memory-mapped model file (weights read from disk)
    breakdown = {}
    for pid, name in ollama_pids().items():
        fp = subprocess.run(["/usr/bin/footprint", "-p", str(pid)], capture_output=True, text=True).stdout
        f = re.search(r"Footprint: (\d+) MB", fp)
        mf = re.search(r"^\s*\S+ \S+\s+([\d.]+) (\w?B)\s+\S+ \S+\s+\d+\s+mapped file$", fp, re.M)
        breakdown[name] = {"footprint_mb": int(f.group(1)) if f else None,
                           "mapped_file": f"{mf.group(1)} {mf.group(2)}" if mf else None}

    cli_rss = re.search(r"(\d+)\s+maximum resident set size", proc.stderr)
    peak = max(samples, key=lambda s: s["total_mb"]) if samples else {}
    per_proc_peak: dict[str, float] = {}
    for s in samples:
        for name, v in s["per_process_mb"].items():
            per_proc_peak[name] = max(per_proc_peak.get(name, 0), v)
    result = {
        "label": label, "command": " ".join(sys.argv[sys.argv.index("--") + 1:]), "cold_start": cold,
        "wall_seconds": wall, "exit_code": proc.returncode,
        "cli_process_max_rss_mb": round(int(cli_rss.group(1)) / 2**20, 1) if cli_rss else None,
        "ollama_peak_total_footprint_mb": peak.get("total_mb"), "ollama_peak_at_s": peak.get("t"),
        "ollama_peak_per_process_mb": per_proc_peak, "samples": len(samples),
        "end_breakdown": breakdown,
        "before": before, "after": {"free": free_percent(),
                                    "ollama_ps": subprocess.run([OLLAMA, "ps"], capture_output=True, text=True).stdout},
        "command_stdout_tail": proc.stdout[-1500:], "sample_series": samples,
    }
    out = ROOT / "evidence" / "measurements" / f"{label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(f"{label}: wall {wall} s · exit {proc.returncode} · CLI max RSS {result['cli_process_max_rss_mb']} MB · "
          f"Ollama peak footprint {result['ollama_peak_total_footprint_mb']} MB at {result['ollama_peak_at_s']} s "
          f"({len(samples)} samples)")
    for name, v in per_proc_peak.items():
        print(f"   peak {v:8.1f} MB  {name}")
    for name, b in breakdown.items():
        print(f"   end: {name}: footprint {b['footprint_mb']} MB, mapped model file {b['mapped_file']}")
    print(f"   free before: {before['free']}\n   free after:  {result['after']['free']}\n   saved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
