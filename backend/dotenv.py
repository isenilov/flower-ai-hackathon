"""Read ``.env`` into the environment, without a dependency.

The model endpoint and its key are per-machine and secret, so they cannot live in the repo,
and typing three ``export`` lines before every command is how a rehearsal ends up running
against no model at all — the failure that once had us debugging a working protocol.

Loaded in two places because a run reaches the nodes by two paths. ``make`` exports these to
its recipes, and ``backend.rounds`` loads them again for the run the page's Run button spawns
— ``frontend/serve.py`` inherits whatever shell started it, which may be neither.

Existing environment always wins: ``CONSORTIUM_MODEL=x make rounds`` overrides the file, and
so does anything already exported. Stdlib only, per the brief's dependency rule — this is
twenty lines and ``python-dotenv`` is a package everyone then has to sync.
"""

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load(path: Path | None = None) -> dict[str, str]:
    """Set every ``KEY=value`` in ``.env`` that is not already in the environment.

    Returns only the names it set, so a caller can say what it picked up without ever
    holding a secret's value. A missing file is normal, not an error: a run with no model is
    a supported mode.
    """
    target = ENV_PATH if path is None else path
    if not target.is_file():
        return {}

    applied: dict[str, str] = {}
    for raw in target.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # `export FOO=bar` as well as `FOO=bar`, so the file can be `source`d by hand too.
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        name, sep, value = line.partition("=")
        if not sep:
            continue
        name = name.strip()
        value = value.strip().strip("'\"")
        if not name or name in os.environ:
            continue
        os.environ[name] = value
        applied[name] = value

    # An empty key is not the same as no key: Qwen rejects an `Authorization: Bearer ` header
    # outright, so a blank line in the file has to mean "unset", not "send nothing".
    for name in ("FLWR_MODEL_API_KEY",):
        if name in os.environ and not os.environ[name].strip():
            del os.environ[name]
            applied.pop(name, None)

    return applied
