"""Static server for the demo page, with caching off.

``python -m http.server`` answers ``If-Modified-Since`` with a 304, which is correct HTTP
and the wrong behaviour here: edit ``app.js`` mid-rehearsal and the browser keeps serving
the version it already has, silently. On demo day that reads as "the change didn't work".

Lives under ``frontend/`` because it belongs to the local demo surface, not the harness —
``fab-exclude`` drops this whole directory from the published app.

    python frontend/serve.py [port]
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8000


class NoCacheHandler(SimpleHTTPRequestHandler):
    """Serve ``frontend/`` and tell the browser never to reuse a response."""

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
        # One line per asset per reload is noise behind a running protocol; keep errors.
        if not str(args[1] if len(args) > 1 else "").startswith("2"):
            super().log_message(format, *args)


def main() -> None:
    """Serve until interrupted."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    handler = partial(NoCacheHandler, directory=str(ROOT))
    with ThreadingHTTPServer(("", port), handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
