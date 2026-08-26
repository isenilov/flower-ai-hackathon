"""A run's trace survives the trip back from SuperGrid inside its own log.

``backend.trace`` has a file sink and a log sink, and on SuperGrid only one of them comes
home: the JSONL is written inside a container and discarded with it, while the log arrives
over ``flwr run --stream``. So the log carries the events too, and ``follow`` rebuilds the
JSONL at this end. That makes the sentinel a contract between the two halves of one module,
and this is what holds the halves together — a drift in either direction leaves the page
following an empty file, which is exactly the failure nobody notices until the demo.

Everything here writes to ``tmp_path``. The real ``frontend/state/`` holds the traces the
scenario selector switches between at the table, and a test that truncated those would be a
test that broke the demo.
"""

import io
import json
from pathlib import Path

from backend import trace


def _log_line(event: dict[str, object]) -> str:
    """One event as it appears in a run's log, prefixes and all."""
    return f"INFO :      {trace.LOG_SENTINEL}{json.dumps(event, separators=(',', ':'))}\n"


def _run_log() -> list[str]:
    """A plausible slice of a streamed run: framework noise, rendered lines, and events."""
    return [
        "INFO :      Starting Flower Simulation\n",
        _log_line({"type": "flower", "seq": 1, "nodes": 3}),
        _log_line({"type": "run_started", "seq": 2, "scenario": {"slug": "healthcare-seismic"}}),
        "(ClientAppActor pid=592) INFO :      firm B   round 1 - grading 13 matches\n",
        _log_line({"type": "round_ended", "seq": 3, "open_gaps": []}),
    ]


def _events(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_events_are_recovered_in_order(tmp_path: Path) -> None:
    """Every event in the log lands in the live trace, in the order it was emitted."""
    recovered = trace.follow(iter(_run_log()), io.StringIO(), state_dir=tmp_path)

    assert recovered == 3
    assert [event["seq"] for event in _events(tmp_path / "trace.jsonl")] == [1, 2, 3]


def test_the_terminal_still_gets_its_log(tmp_path: Path) -> None:
    """Rendered and framework lines pass through; the machine-readable ones do not.

    The demo is a split screen, so the pane has to look the same whether or not a page is
    reading the other sink out of the same stream.
    """
    out = io.StringIO()
    trace.follow(iter(_run_log()), out, state_dir=tmp_path)

    passed = out.getvalue()
    assert "Starting Flower Simulation" in passed
    assert "firm B   round 1 - grading 13 matches" in passed
    assert trace.LOG_SENTINEL not in passed


def test_the_scenario_copy_is_backfilled(tmp_path: Path) -> None:
    """The per-scenario trace gets the events that arrived before the scenario was known.

    ``run_started`` names the scenario and it is the second event, so the copy the selector
    loads is opened one event late and has to be given what it missed.
    """
    trace.follow(iter(_run_log()), io.StringIO(), state_dir=tmp_path)

    copy = tmp_path / "trace-healthcare-seismic.jsonl"
    assert [event["seq"] for event in _events(copy)] == [1, 2, 3]


def test_a_malformed_event_is_shown_rather_than_swallowed(tmp_path: Path) -> None:
    """A sentinel with no event behind it means the format drifted — so it stays visible."""
    out = io.StringIO()
    recovered = trace.follow(
        iter([f"INFO :      {trace.LOG_SENTINEL}not json at all\n"]), out, state_dir=tmp_path
    )

    assert recovered == 0
    assert "not json at all" in out.getvalue()


def test_a_run_that_traced_nothing_is_not_a_success(tmp_path: Path) -> None:
    """No events means the page has nothing to follow, and `make grid` must not pass."""
    assert trace.follow(iter(["INFO :      nothing to see\n"]), io.StringIO(), tmp_path) == 0


def test_emitting_to_the_log_matches_what_follow_reads(tmp_path: Path) -> None:
    """The two halves agree: what `Trace` writes to the log is what `follow` recovers.

    Asserted against `Trace` itself rather than a hand-written line, so the sentinel and the
    event shape cannot drift apart without this failing.
    """
    emitting = trace.Trace(path=tmp_path / "emitted.jsonl", to_log=True)
    # The full field set the round loop emits: `Trace.emit` renders to the terminal on the
    # way past, and that renderer is entitled to the fields its own protocol sends.
    event = emitting.emit("round_ended", round=2, open_gaps=[], stopped="")

    out = io.StringIO()
    trace.follow(iter([_log_line(event)]), out, state_dir=tmp_path)

    assert _events(tmp_path / "trace.jsonl") == [event]
