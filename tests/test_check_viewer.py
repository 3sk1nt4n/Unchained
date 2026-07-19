"""Headless, network-free viewer acceptance checks."""

from __future__ import annotations

from scripts.check_viewer import CORE_SECTIONS, inspect_viewer_html

from unchained.viewer import render_viewer_html


def _complete_report() -> str:
    return "\n".join(
        (
            "# Unchained DFIR Report - COMPLETE",
            "",
            "## Findings",
            "",
            "| ID | Finding | Severity | Investigator | Judge | Tool calls | Evidence spans |",
            "|---|---|---|---|---|---|---|",
            "| F001 | Example | high | CONFIRMED | NEEDS-REVIEW | [t1] | `S001` |",
            "",
            "## Evidence spans",
            "",
            "- `S001` from [t1]",
            "",
            "## Limitations",
            "",
            "- Human review is required.",
            "",
            "## Unresolved questions",
            "",
            "- None.",
        )
    )


def _viewer(report: str) -> str:
    return render_viewer_html(
        run_id="run-viewer-qa",
        status="COMPLETE",
        profile=None,
        summary={"exit_code": 0, "reason": "completed"},
        report_markdown=report,
        audit_entries=[],
    )


def test_headless_viewer_check_accepts_inert_complete_content() -> None:
    sections, errors = inspect_viewer_html(_viewer(_complete_report()), require_complete=True)

    assert errors == ()
    assert sections == CORE_SECTIONS


def test_headless_viewer_check_requires_complete_report_sections() -> None:
    _sections, errors = inspect_viewer_html(_viewer("# Incomplete"), require_complete=True)

    assert any("complete report is missing marker" in value for value in errors)


def test_headless_viewer_check_reuses_positive_inert_policy() -> None:
    active = _viewer(_complete_report()).replace(
        "</body>", '<img src="https://x.invalid">\n</body>'
    )

    _sections, errors = inspect_viewer_html(active, require_complete=True)

    assert any(value.startswith("viewer policy:") for value in errors)
