"""Bounded and raw-quotable model views over retained tool output."""

from __future__ import annotations

import json

from unchained.models import ToolResult


def _result(output: str) -> ToolResult:
    return ToolResult(
        call_id="c1",
        tool_name="vol_netscan",
        arguments={},
        output=output,
        output_sha256="a" * 64,
        status="success",
        started_at="2026-07-20T00:00:00Z",
        ended_at="2026-07-20T00:00:01Z",
        duration_ms=1,
    )


def test_model_output_respects_a_smaller_view_budget_and_keeps_full_output_on_disk() -> None:
    full = "X" * 200_000
    result = _result(full)
    view = result.model_output(8_000)
    assert len(view.encode("utf-8")) <= 8_000
    receipt = json.loads(view)["delivery_receipt"]
    assert receipt["model_view_complete"] is False
    assert receipt["model_view_max_bytes"] == 8_000
    assert receipt["accepted_output_bytes"] == 200_000  # full output still retained
    # The default (no budget) keeps the historical per-tool ceiling.
    assert result.model_output()  # does not raise; bounded at the 64 KiB default


def test_small_output_is_returned_whole_regardless_of_budget() -> None:
    result = _result("only 12 bytes")
    assert result.model_output(2_048) == "only 12 bytes"
    assert result.model_output() == "only 12 bytes"


def test_quotable_view_is_a_raw_byte_exact_prefix_for_exact_span_resolution() -> None:
    # Content with the exact characters that JSON-escaping would corrupt:
    # quotes, backslashes (Windows paths), and newlines.
    full = 'PID 4 System\nC:\\Windows\\System32 "lsass.exe"\n' + ("A" * 200_000)
    result = _result(full)

    view = result.quotable_view(4_000)
    assert len(view.encode("utf-8")) <= 4_000
    # The whole view is a byte-exact prefix of the full output, so any substring
    # the model copies resolves to an exact byte range - no JSON escaping here.
    assert full.encode("utf-8").startswith(view.encode("utf-8"))
    assert 'C:\\Windows\\System32 "lsass.exe"' in view
    assert '"delivery_receipt"' not in view  # never JSON-wrapped

    # A short output is returned whole and unchanged.
    assert _result("PID 4 System").quotable_view(2_048) == "PID 4 System"


def test_quotable_view_never_splits_a_multibyte_character() -> None:
    # A run of 3-byte glyphs; a naive byte cut would leave a partial sequence.
    full = "中" * 5_000  # each is 3 UTF-8 bytes
    view = _result(full).quotable_view(1_000)
    assert view  # decodes cleanly
    assert full.startswith(view)
    assert view == "中" * (len(view))  # only whole glyphs survived
