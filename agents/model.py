"""Model client and on-disk response cache.

Cached during development because SuperGrid contention with ~130 attendees is expected
and venue wifi is a known failure mode.

A firm's agent needs a model to read its own bios, and it can reach one two ways. Under
the published ``AgentApp`` it is handed ``agent.responses.create`` — the Flower Agents
path, and the only one that exists on SuperGrid. Under the federated simulation there is
no ``AgentSession`` at all, so it posts to ``FLWR_MODEL_API_ENDPOINT`` itself. Both speak
Open Responses, so the caller cannot tell them apart.

What crosses the wire here is a firm reading *its own* library with *its own* model. The
bander is what stops raw records reaching a peer; nothing in this module ever emits to one.
"""

import hashlib
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

JSONObject = dict[str, Any]
Reader = Callable[[JSONObject], JSONObject]

ENDPOINT_ENV = "FLWR_MODEL_API_ENDPOINT"
KEY_ENV = "FLWR_MODEL_API_KEY"
CACHE_DIR_ENV = "CONSORTIUM_MODEL_CACHE"

DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "model"

# The shared endpoint answered one round-2 call in ~240s under hackathon load. That is most
# of SuperGrid's 5-minute task budget for a single firm, which is why nodes run concurrently
# and why the cache below is load-bearing rather than a convenience.
DEFAULT_TIMEOUT = 280.0


def _fingerprint(request: JSONObject) -> str:
    """Stable key for a request, so a rehearsed run replays byte for byte."""
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:32]


class HttpReader:
    """Post Open Responses requests straight to a model endpoint.

    Used by the federated surface, which has no ``AgentSession``. Qwen takes no key, so an
    empty ``FLWR_MODEL_API_KEY`` must mean *send no header* rather than send an empty one.
    """

    def __init__(self, endpoint: str, api_key: str = "", timeout: float = DEFAULT_TIMEOUT):
        self.endpoint = endpoint
        self.api_key = api_key
        self.timeout = timeout

    def __call__(self, request: JSONObject) -> JSONObject:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        # Streaming is for a human watching a chat; this is a machine reading a reply.
        payload = {key: value for key, value in request.items() if key != "stream"}
        http_request = urllib.request.Request(
            self.endpoint, data=json.dumps(payload).encode(), headers=headers
        )
        with urllib.request.urlopen(http_request, timeout=self.timeout) as response:
            return json.load(response)


class CachedReader:
    """Wrap a reader with an on-disk cache, and fall back to it when the model is gone.

    Two jobs. It makes a rehearsal cheap, and it makes the demo survive the venue: once a
    request has been answered, losing the endpoint downgrades to a replay instead of a
    failure. ``offline`` skips the network entirely.
    """

    def __init__(self, inner: Reader | None, cache_dir: Path | None = None, offline: bool = False):
        self.inner = inner
        self.offline = offline
        self.cache_dir = cache_dir or Path(os.environ.get(CACHE_DIR_ENV, DEFAULT_CACHE_DIR))

    def _path(self, request: JSONObject) -> Path:
        return self.cache_dir / f"{_fingerprint(request)}.json"

    def __call__(self, request: JSONObject) -> JSONObject:
        path = self._path(request)
        if path.exists():
            return json.loads(path.read_text())
        if self.offline or self.inner is None:
            raise LookupError("No cached model response, and no live model to ask.")

        response = self.inner(request)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(response))
        return response


def resolve_reader(injected: Reader | None = None, offline: bool = False) -> Reader | None:
    """Pick the best available model path, always behind the cache.

    Order: whatever the AgentApp handed us, then the endpoint in the environment, then
    cache-only. ``None`` means there is no model at all — the caller must degrade rather
    than raise, because a harness with no model still has a coverage matrix to print.
    """
    if offline:
        return CachedReader(None, offline=True)
    if injected is not None:
        return CachedReader(injected)

    endpoint = os.environ.get(ENDPOINT_ENV, "").strip()
    if endpoint:
        return CachedReader(HttpReader(endpoint, os.environ.get(KEY_ENV, "").strip()))

    cache_only = CachedReader(None, offline=True)
    return cache_only if cache_only.cache_dir.is_dir() else None


def extract_text(response: JSONObject) -> str:
    """Pull the assistant's text out of an Open Responses reply.

    Reasoning models put their scratchpad in ``output`` alongside the answer, so items of
    type ``reasoning`` are skipped — taking ``output[0]`` gets you the scratchpad.
    """
    chunks: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict) or item.get("type") == "reasoning":
            continue
        content = item.get("content")
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            chunks += [
                part["text"]
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
    return "\n".join(chunks).strip()


def extract_json(response: JSONObject) -> JSONObject:
    """Parse a JSON object out of the model's text, tolerating fences and preamble."""
    text = extract_text(response)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"No JSON object in model reply: {text[:200]!r}")
    return json.loads(text[start : end + 1])
