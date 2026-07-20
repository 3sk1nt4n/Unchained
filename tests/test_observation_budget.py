"""The batched-observation byte budget that lets a large opening fit the token cap."""

from __future__ import annotations

import json

from unchained.agent import _per_observation_bytes
from unchained.models import MODEL_TOOL_OUTPUT_MAX_BYTES, ToolResult


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


def test_per_observation_bytes_shrinks_for_a_large_batch_and_caps_for_a_small_one() -> None:
    # A whole 12-tool opening against a 100k-ish remaining budget must feed a
    # small prefix each, well under the per-tool ceiling.
    small = _per_observation_bytes(97_700, 12)
    assert 2_048 <= small < MODEL_TOOL_OUTPUT_MAX_BYTES
    assert small * 12 // 3 < 97_700  # observation tokens leave room for overhead
    # A generous budget with few observations reaches the per-tool ceiling.
    assert _per_observation_bytes(400_000, 6) == MODEL_TOOL_OUTPUT_MAX_BYTES
    # Always floored so every tool shows something, even when nearly out.
    assert _per_observation_bytes(1_000, 12) == 2_048
    assert _per_observation_bytes(0, 4) == 2_048


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
