"""Terminal colour for the demo's left-hand pane, matched to the frontend's palette.

The split screen only reads as one system if firm B is the same amber in the terminal as
it is on the page, so every colour here is the literal token from ``frontend/styles.css``
rather than one of the sixteen the terminal offers. Truecolor when the terminal advertises
it, the nearest xterm-256 cube entry when it does not.

Colour carries meaning here, it does not decorate: ``FLOWER`` is always the framework doing
the work, ``GAP`` and ``OK`` are always the red and green of the coverage matrix, and
``FIRM_B`` amber is always the gap travelling back. Someone two metres from the screen
should be able to read the run off the colours before reading a word of it.
"""

import os
import sys
from logging import INFO

from flwr.common.logger import log

# ``frontend/styles.css`` :root, verbatim. FLOWER is the one colour with no counterpart on
# the page: nothing there stands for the framework, and it must not be mistaken for firm A.
FLOWER = (34, 211, 238)
FIRM = ((76, 141, 255), (245, 165, 36), (168, 85, 247))  # --firm-a / -b / -c
OK = (47, 191, 113)
GAP = (240, 67, 79)
INK = (232, 237, 246)
DIM = (141, 155, 179)
FAINT = (91, 105, 128)

_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"


def enabled() -> bool:
    """Whether to emit escape codes at all.

    Flower logs to stderr, so that is the stream whose terminal-ness decides. Piping the
    log to a file or through ``grep`` must yield plain text — the trace is read by people
    after the demo too, and half of them will have redirected it.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stderr.isatty()


def _fg(rgb: tuple[int, int, int]) -> str:
    """Foreground escape for one colour, at the best depth this terminal admits."""
    red, green, blue = rgb
    if os.environ.get("COLORTERM") in ("truecolor", "24bit"):
        return f"\x1b[38;2;{red};{green};{blue}m"
    # The 6×6×6 cube: Terminal.app and anything else without COLORTERM still lands close
    # enough that firm B stays orange and the gap stays red.
    cube = [round(channel / 255 * 5) for channel in (red, green, blue)]
    return f"\x1b[38;5;{16 + 36 * cube[0] + 6 * cube[1] + cube[2]}m"


def paint(text: str, rgb: tuple[int, int, int] | None = None, *, bold: bool = False) -> str:
    """Colour ``text``, or return it untouched when colour is off.

    Width is preserved either way, so a caller can pad a column before or after painting
    it without the escape codes throwing the alignment off.
    """
    if not text or not enabled() or (rgb is None and not bold):
        return text
    prefix = (_BOLD if bold else "") + (_fg(rgb) if rgb else "")
    return f"{prefix}{text}{_RESET}"


def firm_tone(firm: str) -> tuple[int, int, int]:
    """The lane colour the page gives this firm, so both panes agree on who is who."""
    index = ord(firm[-1].upper()) - ord("A") if firm.startswith("FIRM_") else 0
    return FIRM[index % len(FIRM)]


# ----------------------------------------------------------------- node-side lines
#
# Both rounds' model work happens inside a SuperNode, and both report it the same way. Ray
# forwards an actor's stdout to the driver with its pid attached, so these arrive in the
# demo's terminal pane already labelled by node — which is the point. It is visible proof
# that the prose was read on the firm's own node and that only a verdict left it.

# Same width as the coordinator's tag gutter in `backend.trace`, so node lines and
# coordinator lines line up in one column even though Ray prefixes only the former.
_GUTTER = 9


def say(line: str) -> None:
    """Log a node-side line and flush, so it arrives while it is still true.

    A ClientAppActor's stderr is a pipe, not a terminal, so Python block-buffers it and Ray
    forwards nothing until the actor is torn down — which puts "firm B found it" on screen
    *after* the verdict. Flushing is what makes a node-side beat land in its own round.
    """
    log(INFO, "%s", line)
    sys.stderr.flush()
    sys.stdout.flush()


def node_line(firm: str, detail: str, tone: tuple[int, int, int] | None = None) -> str:
    """A node-side line in the firm's own lane colour, matching the coordinator's columns."""
    name = firm.replace("FIRM_", "firm ")
    return paint(f"{name:<{_GUTTER}}", firm_tone(firm), bold=True) + paint(detail, tone)


def took(seconds: float, replay: bool) -> str:
    """How long the model took, or that it was never asked because the answer was on disk.

    Asked of the cache rather than inferred from the duration: a rehearsal runs entirely off
    disk, and a bare "0ms" reads as a model that was never consulted at all.
    """
    if replay:
        return "from cache"
    return f"{seconds * 1000:.0f}ms" if seconds < 1 else f"{seconds:.1f}s"
