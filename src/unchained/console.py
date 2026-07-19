"""Deterministic, dependency-free terminal styling for judge-facing output.

Styling is display-only. It never carries authority, never reaches audited
artifacts, and collapses to the exact legacy plain text whenever the target
stream is not an interactive terminal, ``NO_COLOR`` is set, or the operator
passed ``--no-color``. Scripted consumers therefore keep byte-identical lines.
"""

from __future__ import annotations

import os
import sys
from typing import TextIO

_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"
_DIM_ATTR = "\x1b[2m"
_REVERSE = "\x1b[7m"

_PRIMARY = "\x1b[38;5;45m"
_ACCENT = "\x1b[38;5;141m"
_OK = "\x1b[38;5;78m"
_WARN = "\x1b[38;5;214m"
_FAIL = "\x1b[38;5;203m"
_MUTED = "\x1b[38;5;245m"
_WHITE = "\x1b[38;5;255m"

_STATUS_COLORS = {
    "COMPLETE": _OK,
    "VALID": _OK,
    "PASS": _OK,
    "PARTIAL": _WARN,
    "INVALID": _FAIL,
    "FATAL": _FAIL,
    "FAIL": _FAIL,
}

_GLYPH_FALLBACK = str.maketrans(
    {
        "▸": ">",
        "▪": "*",
        "●": "*",
        "◆": "*",
        "─": "-",
        "━": "=",
        "│": "|",
        "┃": "|",
        "┌": "+",
        "┐": "+",
        "└": "+",
        "┘": "+",
        "┏": "+",
        "┓": "+",
        "┗": "+",
        "┛": "+",
        "✓": "OK",
        "✗": "X",
        "▲": "!",
        "↑": "^",
        "↓": "v",
        "·": "-",
        "—": "-",
        "…": "...",
        "⏱": "t",
        "⚒": "*",
    }
)


def _stream_supports_glyphs(stream: TextIO) -> bool:
    encoding = getattr(stream, "encoding", None)
    if not encoding:
        return False
    try:
        "▸✓✗▲│─◆·↑↓⚒⏱┏┓┗┛━".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return False
    return True


def styling_enabled(stream: TextIO, *, no_color: bool = False) -> bool:
    """True only for an interactive terminal with color not explicitly refused."""

    if no_color or os.environ.get("NO_COLOR"):
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


class Console:
    """A small styled writer bound to one output stream."""

    def __init__(self, stream: TextIO | None = None, *, no_color: bool = False) -> None:
        self.stream = stream if stream is not None else sys.stderr
        self.enabled = styling_enabled(self.stream, no_color=no_color)
        self._glyphs = _stream_supports_glyphs(self.stream)

    def _emit(self, text: str) -> None:
        if not self._glyphs:
            text = text.translate(_GLYPH_FALLBACK)
        print(text, file=self.stream, flush=True)

    def _paint(self, text: str, *styles: str) -> str:
        if not self.enabled:
            return text
        return f"{''.join(styles)}{text}{_RESET}"

    def banner(self, title: str, tagline: str) -> None:
        width = max(len(title), len(tagline)) + 6
        top = "┏" + "━" * width + "┓"
        bottom = "┗" + "━" * width + "┛"
        self._emit(self._paint(top, _PRIMARY, _BOLD))
        self._emit(
            self._paint("┃", _PRIMARY, _BOLD)
            + self._paint(title.center(width), _WHITE, _BOLD)
            + self._paint("┃", _PRIMARY, _BOLD)
        )
        self._emit(
            self._paint("┃", _PRIMARY, _BOLD)
            + self._paint(tagline.center(width), _ACCENT)
            + self._paint("┃", _PRIMARY, _BOLD)
        )
        self._emit(self._paint(bottom, _PRIMARY, _BOLD))

    def phase(self, label: str) -> None:
        bar = "─" * max(4, 62 - len(label))
        self._emit("")
        self._emit(self._paint(f"◆ {label} {bar}", _ACCENT, _BOLD))

    def step(self, message: str, *, elapsed: str | None = None) -> None:
        prefix = self._paint("▸", _PRIMARY, _BOLD)
        suffix = f"  {self._paint(f'⏱ {elapsed}', _MUTED)}" if elapsed else ""
        self._emit(f"{prefix} {message}{suffix}")

    def detail(self, message: str) -> None:
        self._emit(f"  {self._paint(message, _MUTED)}")

    def ok(self, message: str) -> None:
        self._emit(f"{self._paint('✓', _OK, _BOLD)} {message}")

    def warn(self, message: str) -> None:
        self._emit(f"{self._paint('▲', _WARN, _BOLD)} {self._paint(message, _WARN)}")

    def fail(self, message: str) -> None:
        self._emit(f"{self._paint('✗', _FAIL, _BOLD)} {self._paint(message, _FAIL)}")

    def kv(self, label: str, value: str, *, pad: int = 14) -> None:
        self._emit(f"  {self._paint(label.ljust(pad), _MUTED)} {self._paint(value, _WHITE)}")

    def badge(self, status: str) -> str:
        color = _STATUS_COLORS.get(status.upper(), _ACCENT)
        return self._paint(f" {status.upper()} ", color, _REVERSE, _BOLD)

    def rule(self) -> None:
        self._emit(self._paint("─" * 66, _MUTED))

    def line(self, text: str) -> None:
        """Write one pre-composed line through glyph fallback handling."""

        self._emit(text)
