"""Shared test helpers for the entirely offline acceptance suite."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_saved_key_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Keep every test blind to any real operator key saved via `sentinel key`."""

    import unchained.model as model_module

    monkeypatch.setattr(
        model_module,
        "default_api_key_file",
        lambda: tmp_path / "isolated-sentinel-key" / "openai_api_key",
    )


@dataclass
class ManualClock:
    """A monotonic clock that advances without sleeping."""

    now: float = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds
