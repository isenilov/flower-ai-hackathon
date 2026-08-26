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
