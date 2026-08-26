"""Static server for the demo page, plus the one endpoint that starts a run.

Two jobs beyond serving files.

**Caching off.** ``python -m http.server`` answers ``If-Modified-Since`` with a 304, which
is correct HTTP and the wrong behaviour here: edit ``app.js`` mid-rehearsal and the browser
keeps serving the version it already has, silently. On demo day that reads as "the change
didn't work".

**A run button.** The demo is a split screen — this process in a terminal pane, the page
beside it — so ``POST /run`` spawns ``python -m backend.rounds`` with **stdout inherited**.
That is the whole trick: the protocol's log lands in the same pane this server is running
in, so the terminal half of the screen fills up as the page animates, and neither half is a
recording of the other.

Lives under ``frontend/`` because it belongs to the local demo surface, not the harness —
``fab-exclude`` drops this whole directory from the published app.

    python frontend/serve.py [port]
"""

import json
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DEFAULT_PORT = 8000

# This process spawns subprocesses on an unauthenticated POST, so it answers the loopback
# interface only. A demo on conference wifi is not a place to listen on 0.0.0.0.
HOST = "127.0.0.1"


def _slugs() -> list[str]:
    """The scenarios that exist, so an unknown slug is a 400 and not a stack trace.

    Read from the catalogue rather than kept in a list here: the manifest is the one place
    that knows, and a mirror of it would go stale the first time someone adds a scenario.
    """
    sys.path.insert(0, str(REPO))
    from backend.scenarios import catalogue

    return sorted(catalogue())


class Runner:
    """Owns the one protocol run this server will admit at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self.scenario = ""

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def state(self) -> dict[str, object]:
        """What the page's Run button renders itself from."""
        code = None if self._process is None else self._process.poll()
        return {"running": self.running, "scenario": self.scenario, "exit": code}

    def start(self, scenario: str, rounds: int, model: str) -> tuple[int, dict[str, object]]:
        """Spawn a run, or refuse if one is already going."""
        with self._lock:
            if self.running:
                return 409, {"error": "a run is already going", **self.state()}

            known = _slugs()
            if scenario and scenario not in known:
                return 400, {"error": f"unknown scenario {scenario!r}", "scenarios": known}

            command = [
                sys.executable,
                "-m",
                "backend.rounds",
                "--rounds",
                str(rounds),
                "--scenario",
                scenario,
                "--quiet",
            ]
            # Only when the caller named one. `--model ''` would *override* CONSORTIUM_MODEL
            # with nothing, which is the failure that once had us debugging a working
            # protocol: round 2 finds nothing and the bid reads non-compliant.
            if model:
                command += ["--model", model]
            # No `shell=True` and no string command: `scenario` reached us over HTTP, and
            # the only thing standing between it and a shell should be that there isn't one.
            self._process = subprocess.Popen(command, cwd=REPO)
            self.scenario = scenario
            return 202, self.state()


class DemoHandler(SimpleHTTPRequestHandler):
    """Serve ``frontend/``, never cache, and expose ``/run``."""

    runner = Runner()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/run":
            self.send_error(404)
            return

        query = parse_qs(urlparse(self.path).query)
        status, body = self.runner.start(
            scenario=(query.get("scenario") or [""])[0],
            rounds=int((query.get("rounds") or ["3"])[0]),
            model=(query.get("model") or [""])[0],
        )
        self._json(status, body)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/run":
            self._json(200, self.runner.state())
            return
        super().do_GET()

    def _json(self, status: int, body: dict[str, object]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_head(self) -> BytesIO | BinaryIO | None:
        # Dropping the validators from the *request* is what forces a full response.
        # Withholding Last-Modified on the way out is not enough: the browser has already
        # cached one, and `send_head` honours whatever If-Modified-Since it is handed.
        del self.headers["If-Modified-Since"]
        del self.headers["If-None-Match"]
        return super().send_head()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        # One line per asset per reload is noise in a pane that is showing a protocol; the
        # page polls the trace four times a second, so this would drown everything.
        if not str(args[1] if len(args) > 1 else "").startswith("2"):
            super().log_message(format, *args)


def main() -> None:
    """Serve until interrupted."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    handler = partial(DemoHandler, directory=str(ROOT))
    with ThreadingHTTPServer((HOST, port), handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
