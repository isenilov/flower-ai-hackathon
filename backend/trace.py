"""Protocol event trace — one emit point, three sinks.

The round loop is the only thing that knows what crossed the boundary and when, so it is
the only thing that emits. Each event fans out to three places:

* **JSONL** at ``frontend/state/trace.jsonl`` — what the visualisation reads. A file, not
  a socket: the frontend is served by ``python -m http.server`` and polls, so there is no
  bridge process to babysit and no network dependency during a demo.
* **the terminal**, via Flower's logger — the only renderer that survives publishing, since
  Hub keeps ``.py`` and drops the frontend entirely.
* **Flower's own event stream**, when the runtime offers one. ``RuntimeAgentSession`` has a
  ``push_run_events`` that reaches every ``Control.StreamRunEvents`` consumer, ``flwr chat``
  included. It is absent from the public ``AgentSession`` ABC, so this is strictly a bonus:
  guarded by ``hasattr``, and a failure to push never interrupts a run.

Byte counts are the point of the ``bytes`` fields, not decoration. The safety claim is that
no record content crosses before authorisation, and that is only checkable if the wire is
measured — so ``banded`` and ``record`` bytes are counted separately.
"""

import json
import time
from collections.abc import Sequence
from logging import INFO, WARNING
from pathlib import Path
from typing import Any, Protocol

from flwr.common.logger import log

TRACE_PATH = Path(__file__).resolve().parent.parent / "frontend" / "state" / "trace.jsonl"

# Trace format version. The frontend refuses a trace it does not understand rather than
# rendering half a run — this is the contract between backend/ and frontend/.
TRACE_VERSION = 1


class EventSink(Protocol):
    """The slice of ``RuntimeAgentSession`` this module uses, if the runtime provides it."""

    def push_run_events(self, events: Sequence[dict[str, Any]]) -> None:
        """Push structured run events to ``Control.StreamRunEvents`` consumers."""


class Trace:
    """Append-only event log for one protocol run.

    Construct once per run and pass it down; ``emit`` is the whole surface.
    """

    def __init__(self, path: Path | None = None, session: object | None = None) -> None:
        self._path = TRACE_PATH if path is None else path
        self._session = session if hasattr(session, "push_run_events") else None
        self._forward_failed = False
        self._origin = time.monotonic()
        self._seq = 0
        # Wall clock, not the monotonic origin: a page following the file needs to tell one
        # run from the next, and every run's first `t_ms` is the same handful of ms.
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("")

    def emit(self, event_type: str, **fields: Any) -> dict[str, Any]:
        """Record one event and return it."""
        self._seq += 1
        event = {
            "type": event_type,
            "seq": self._seq,
            "t_ms": round((time.monotonic() - self._origin) * 1000, 1),
            **fields,
        }

        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, separators=(",", ":")) + "\n")

        line = _terminal_line(event)
        if line:
            log(INFO, "%s", line)

        self._forward(event)
        return event

    def _forward(self, event: dict[str, Any]) -> None:
        """Mirror the event into Flower's run-event stream, if this runtime has one."""
        if self._session is None or self._forward_failed:
            return
        try:
            self._session.push_run_events([event])  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - a telemetry sink must never fail a run
            # Stop after the first failure: the stream is unavailable, not flaky, and one
            # warning per run is signal where one per event is noise.
            self._forward_failed = True
            log(WARNING, "run-event forwarding disabled: %s", exc)


# ------------------------------------------------------------------ terminal rendering

_FIRM = "{:<11}"


def _terminal_line(event: dict[str, Any]) -> str:
    """Render one event as a terminal line, or '' for events the log should skip."""
    kind = event["type"]

    if kind == "run_started":
        firms = ", ".join(event["firms"])
        return (
            f"trace v{event['version']} — {len(event['requirements'])} requirements, firms {firms}"
        )

    if kind == "round_started":
        gap = ",".join(event["gap"]) or "—"
        return f"round {event['round']}  gap broadcast: {gap}"

    if kind == "broadcast":
        gap = ",".join(event["gap"]) or "—"
        return (
            f"  coordinator -> {_FIRM.format('all firms')} QUERY  "
            f"requirements={event['requirements']}  gap={gap:<10} {_bytes(event['bytes'])}"
        )

    if kind == "reply":
        new = ",".join(event["new_requirements"])
        note = f"  new={new}" if new else ""
        return (
            f"  {_FIRM.format(event['firm'])} -> coordinator REPLY  "
            f"attestations={event['attestations']:<4} {_bytes(event['bytes'])}{note}"
        )

    if kind == "matrix":
        cells = "  ".join(f"{row['id']}{'ok' if row['met'] else 'GAP':>4}" for row in event["rows"])
        return f"  matrix  {cells}"

    if kind == "run_ended":
        gaps = ", ".join(event["open_gaps"]) or "none"
        return (
            f"trace complete — {event['rounds_run']} rounds, open gaps: {gaps}, "
            f"banded on wire {_bytes(event['banded_bytes'])}, "
            f"record bytes {event['record_bytes']}"
        )

    return ""


def _bytes(count: int) -> str:
    """Human-readable byte count, right-padded to keep the log columns aligned."""
    if count < 1024:
        return f"{count} B"
    return f"{count / 1024:.1f} kB"
