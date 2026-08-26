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

from backend import ansi

STATE_DIR = Path(__file__).resolve().parent.parent / "frontend" / "state"
TRACE_PATH = STATE_DIR / "trace.jsonl"
INDEX_PATH = STATE_DIR / "scenarios.json"

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

    def __init__(
        self,
        path: Path | None = None,
        session: object | None = None,
        scenario: str = "",
    ) -> None:
        self._session = session if hasattr(session, "push_run_events") else None
        self._forward_failed = False
        self._origin = time.monotonic()
        self._seq = 0
        # Wall clock, not the monotonic origin: a page following the file needs to tell one
        # run from the next, and every run's first `t_ms` is the same handful of ms.
        self.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")

        # Two paths, same bytes. `trace.jsonl` is the one a following page tails; the
        # per-scenario copy is what the scenario selector loads, so switching scenarios at
        # the table does not mean re-running one.
        self._paths = [TRACE_PATH if path is None else path]
        if scenario and path is None:
            self._paths.append(STATE_DIR / f"trace-{scenario}.jsonl")

        for target in self._paths:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("")
        write_index()

    def emit(self, event_type: str, **fields: Any) -> dict[str, Any]:
        """Record one event and return it."""
        self._seq += 1
        event = {
            "type": event_type,
            "seq": self._seq,
            "t_ms": round((time.monotonic() - self._origin) * 1000, 1),
            **fields,
        }

        line = json.dumps(event, separators=(",", ":")) + "\n"
        for target in self._paths:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(line)

        rendered = _terminal_line(event)
        if rendered:
            log(INFO, "%s", rendered)

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


def write_index() -> Path:
    """List every scenario and whether a trace for it is on disk.

    The page cannot read ``data/scenarios.json`` — only ``frontend/`` is served — so the
    selector reads this instead. Rewritten on every run, so a scenario becomes selectable
    the moment it has been run once.
    """
    from backend.scenarios import catalogue, default_slug

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "slug": scenario.slug,
            "title": scenario.title,
            "headline": scenario.headline,
            "trace": f"trace-{scenario.slug}.jsonl",
            "available": (STATE_DIR / f"trace-{scenario.slug}.jsonl").exists(),
        }
        for scenario in catalogue().values()
    ]
    INDEX_PATH.write_text(
        json.dumps({"default": default_slug(), "scenarios": entries}, indent=2) + "\n"
    )
    return INDEX_PATH


# ------------------------------------------------------------------ terminal rendering
#
# The demo is a split screen: this pane on the left, the page on the right. So the columns
# are fixed and the colours are the page's own tokens (see `backend.ansi`) — a judge should
# be able to look from one to the other and see the same run, not two renderings of it.

# Tag gutter. Every line starts with what kind of thing it is, in one word, so the eye can
# skip down the left edge and find the round boundaries without reading.
_TAG = 9


def _tag(word: str, rgb: tuple[int, int, int] | None = None, *, bold: bool = False) -> str:
    """One tag, padded before it is painted so escape codes never shift the column."""
    return ansi.paint(f"{word:<{_TAG}}", rgb, bold=bold)


def _cell(row: dict[str, Any]) -> str:
    """One coverage cell, red or green, the same two colours the matrix uses on screen."""
    met = row["met"]
    return ansi.paint(f"{row['id']} {'ok' if met else 'GAP'}", ansi.OK if met else ansi.GAP)


def _terminal_line(event: dict[str, Any]) -> str:
    """Render one event as a terminal line, or '' for events the log should skip."""
    kind = event["type"]

    if kind == "flower":
        # No model is a supported mode, not a fault — but it decides whether round 2 has
        # anything to find, so the pane says which it is rather than leaving it to be
        # inferred from an empty round 2 twenty seconds later.
        model = event.get("model") or ""
        note = (
            ansi.paint(f"  model {model}", ansi.FIRM[1])
            if model
            else ansi.paint("  no model - round 1 only, the gap will stay open", ansi.GAP)
        )
        return (
            _tag("flower", ansi.FLOWER, bold=True)
            + ansi.paint(
                f"flwr {event['flwr']} · {event['runtime']} · {event['transport']} · "
                f"{event['nodes']} SuperNodes, one process each",
                ansi.FLOWER,
            )
            + note
        )

    if kind == "run_started":
        scenario = event["scenario"]
        return _tag("coord", ansi.INK, bold=True) + (
            f"{ansi.paint(scenario['slug'], ansi.INK, bold=True)} · "
            f"{len(event['requirements'])} requirements · {len(event['firms'])} firms · "
            f"trace v{event['version']}"
        )

    if kind == "round_started":
        gap = ",".join(event["gap"])
        tone = ansi.FIRM[1] if gap else ansi.INK
        note = (
            f"gap {gap} goes back to the firms — the hole, never the evidence"
            if gap
            else "firms answer from declared fields only — no gap known yet"
        )
        # The rule takes Flower's `INFO :` prefix so the round line itself starts at column
        # zero — an empty log record would print the prefix onto a blank line instead, and a
        # pane with one of those per round reads as noise.
        rule = ansi.paint("-" * 78, ansi.FAINT)
        return (
            rule + "\n" + _tag(f"round {event['round']}", tone, bold=True) + ansi.paint(note, tone)
        )

    if kind == "broadcast":
        # This event *is* the Flower call, so it wears the framework's colour. The gap's own
        # byte count rides along because it is the safety claim: 2 B out, kilobytes back.
        gap = ",".join(event["gap"])
        detail = (
            f"{event['transport']}.send_and_receive · {event['messages']} × "
            f"Message({event['message_type'].upper()}) · {_bytes(event['bytes'])} out"
        )
        aside = ansi.paint(f"  (gap {gap} = {event['gap_bytes']} B)", ansi.FIRM[1]) if gap else ""
        return _tag("flower", ansi.FLOWER) + ansi.paint(detail, ansi.FLOWER) + aside

    if kind == "reply":
        firm = event["firm"]
        tone = ansi.firm_tone(firm)
        new = ",".join(event["new_requirements"])
        note = (
            ansi.paint(f"   new {new}", ansi.OK if event["round"] > 1 else ansi.DIM) if new else ""
        )
        return (
            _tag(f"  {_short(firm)}", tone, bold=True)
            + ansi.paint("-> coordinator", ansi.DIM)
            + f"   {event['attestations']:>3} attestations   {_bytes(event['bytes']):>7}"
            + note
        )

    if kind == "matrix":
        closed = ",".join(event.get("closed") or [])
        cells = "  ".join(_cell(row) for row in event["rows"])
        won = ansi.paint(f"   {closed} closed", ansi.OK, bold=True) if closed else ""
        return _tag("  matrix", ansi.DIM) + cells + won

    if kind == "round_ended":
        # The coordinator's decision, and the only one it makes alone: broadcast the gap
        # again, or stop. Silent until now, which read as the round loop having no author.
        gaps = ",".join(event["open_gaps"])
        stopped = event["stopped"]
        if not gaps:
            detail, tone = f"every requirement met - stopping at round {event['round']}", ansi.OK
        elif stopped == "no-new-evidence":
            detail, tone = (
                f"{gaps} still unmet and round {event['round']} found nothing new - stopping",
                ansi.GAP,
            )
        else:
            detail, tone = f"{gaps} unmet - going back to the firms with the gap", ansi.FIRM[1]
        return _tag("coord", ansi.INK, bold=True) + ansi.paint(detail, tone)

    if kind == "run_ended":
        compliant = event["compliant"]
        tone = ansi.OK if compliant else ansi.GAP
        gaps = ", ".join(event["open_gaps"]) or "none"
        return (
            ansi.paint("-" * 78, ansi.FAINT)
            + "\n"
            + _tag("verdict", tone, bold=True)
            + ansi.paint("compliant" if compliant else "NON-COMPLIANT", tone, bold=True)
            + f" · {event['rounds_run']} rounds · open gaps {gaps}"
            + f" · {_bytes(event['banded_bytes'])} banded on the wire · "
            + ansi.paint(f"{event['record_bytes']} B of record content", ansi.OK)
        )

    return ""


def _short(firm: str) -> str:
    """`FIRM_A` as the page writes it, so both panes name the same lane the same way."""
    return firm.replace("FIRM_", "firm ") if firm.startswith("FIRM_") else firm


def _bytes(count: int) -> str:
    """Human-readable byte count."""
    if count < 1024:
        return f"{count} B"
    return f"{count / 1024:.1f} kB"
