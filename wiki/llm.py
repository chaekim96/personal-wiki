"""The only file that talks to the model. Local mode = Ollama on this Mac (localhost:11434).

Uses Python's built-in urllib, so there is no client library to explain. Every call goes to
localhost; nothing here can reach the internet.
"""
import json
import time
import urllib.error
import urllib.request

from . import config


class ModelUnavailable(RuntimeError):
    """Raised with a human-readable fix when Ollama or the model is not available."""


def _post(path: str, payload: dict, timeout: float = 600) -> dict:
    req = urllib.request.Request(
        config.OLLAMA_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if e.code == 404 and "not found" in body:
            model = payload.get("model")
            raise ModelUnavailable(
                f"Model '{model}' is not downloaded in Ollama.\n"
                f"Fix (needs internet once): /Applications/Ollama.app/Contents/Resources/ollama pull {model}"
            ) from None
        raise ModelUnavailable(f"Ollama returned HTTP {e.code}: {body[:300]}") from None
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise ModelUnavailable(
            f"Cannot reach Ollama at {config.OLLAMA_URL} ({e}).\n"
            "Fix: open /Applications/Ollama.app (or run `ollama serve`), then try again."
        ) from None


def chat(messages: list[dict], *, schema: dict | None = None, temperature: float = 0.2,
         num_predict: int = 1024) -> dict:
    """Send a list of {role, content} messages to local Gemma.

    schema: optional JSON Schema; Ollama then forces the reply to be valid JSON of that shape.
    Returns {"text", "seconds", "prompt_tokens", "output_tokens"}.
    """
    payload = {
        "model": config.MODEL,
        "messages": messages,
        "stream": False,
        "think": False,          # Gemma 4 "thinks" by default; off = faster, shorter replies
        "options": {"temperature": temperature, "num_ctx": config.NUM_CTX, "num_predict": num_predict},
    }
    if schema:
        payload["format"] = schema
    start = time.perf_counter()
    data = _post("/api/chat", payload)
    return {
        "text": data["message"]["content"],
        "seconds": round(time.perf_counter() - start, 2),
        "prompt_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),
    }


def chat_json(messages: list[dict], schema: dict, **kw) -> tuple[dict, dict]:
    """Like chat(), but parses the JSON reply. Returns (parsed, call_info)."""
    info = chat(messages, schema=schema, **kw)
    try:
        return json.loads(info["text"]), info
    except json.JSONDecodeError:
        raise ModelUnavailable(f"Model returned invalid JSON: {info['text'][:300]}") from None


def embed(texts: list[str]) -> list[list[float]]:
    """Turn texts into meaning-vectors with the local embedding model (one vector per text)."""
    data = _post("/api/embed", {"model": config.EMBED_MODEL, "input": texts}, timeout=300)
    return data["embeddings"]


def check_model(model: str = config.MODEL) -> str:
    """Fail early with a clear message if Ollama is down or the model is missing."""
    try:
        with urllib.request.urlopen(config.OLLAMA_URL + "/api/tags", timeout=5) as resp:
            names = [m["name"] for m in json.load(resp)["models"]]
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        raise ModelUnavailable(
            f"Cannot reach Ollama at {config.OLLAMA_URL} ({e}).\n"
            "Fix: open /Applications/Ollama.app (or run `ollama serve`), then try again."
        ) from None
    if model not in names:
        raise ModelUnavailable(
            f"Model '{model}' is not downloaded. Installed: {', '.join(names) or 'none'}.\n"
            f"Fix (needs internet once): ollama pull {model}"
        )
    return model
