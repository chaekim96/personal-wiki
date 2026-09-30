"""Save every search/ask/chat run to evidence/runs/ so results can be inspected without rerunning."""
import datetime as dt
import json

from . import config


def save_run(mode: str, record: dict) -> str:
    """Write one run as JSON. Returns the path relative to the project root."""
    folder = config.EVIDENCE / "runs"
    folder.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now()
    path = folder / f"{now.strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{mode}.json"
    model = "none (retrieval only)" if mode == "search" else config.MODEL
    record = {"mode": mode, "execution": "local", "model": model,
              "time": now.isoformat(timespec="seconds"), **record}
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path.relative_to(config.ROOT).as_posix()
