#!/usr/bin/env python3
"""Verify and inspect a Unchained proof viewer without network or a web server."""

from __future__ import annotations

import argparse
import json
import stat
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from unchained.verify import verify_run
from unchained.viewer_policy import validate_inert_viewer_html

MAX_VIEWER_BYTES = 16 * 1024 * 1024
CORE_SECTIONS = (
    "Protocol timeline",
    "Custody receipt",
    "Evidence inventory",
    "Typed tool receipts",
    "Terminal context",
    "Analyst report",
)
COMPLETE_REPORT_MARKERS = (
    "# Unchained DFIR Report - COMPLETE",
    "## Findings",
    "| ID | Finding | Severity | Investigator | Judge | Tool calls | Evidence spans |",
    "## Evidence spans",
    "## Limitations",
    "## Unresolved questions",
)


class _ViewerProbe(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture: str | None = None
        self._buffer: list[str] = []
        self.sections: list[str] = []
        self.report = ""

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        if tag in {"h2", "pre"}:
            self._capture = tag
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != self._capture:
            return
        value = "".join(self._buffer).strip()
        if tag == "h2":
            self.sections.append(value)
        elif tag == "pre":
            self.report = value
        self._capture = None
        self._buffer = []


@dataclass(frozen=True, slots=True)
class ViewerCheckResult:
    passed: bool
    terminal_status: str | None
    verified_artifacts: int
    verified_audit_entries: int
    sections: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "passed": self.passed,
            "terminal_status": self.terminal_status,
            "verified_artifacts": self.verified_artifacts,
            "verified_audit_entries": self.verified_audit_entries,
            "viewer": {
                "inert_policy_passed": not any(
                    value.startswith("viewer policy:") for value in self.errors
                ),
                "network_or_server_required": False,
                "sections": list(self.sections),
            },
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def inspect_viewer_html(
    text: str,
    *,
    require_complete: bool,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    errors = [f"viewer policy: {value}" for value in validate_inert_viewer_html(text)]
    probe = _ViewerProbe()
    try:
        probe.feed(text)
        probe.close()
    except Exception as exc:  # pragma: no cover - defensive parser boundary
        errors.append(f"viewer inspection failed safely: {type(exc).__name__}")
        return tuple(probe.sections), tuple(errors)

    for section in CORE_SECTIONS:
        if section not in probe.sections:
            errors.append(f"viewer is missing section: {section}")
    if require_complete:
        for marker in COMPLETE_REPORT_MARKERS:
            if marker not in probe.report:
                errors.append(f"complete report is missing marker: {marker}")
    return tuple(probe.sections), tuple(errors)


def check_bundle_viewer(
    run_directory: Path,
    *,
    require_complete: bool = False,
    require_live_gpt56: bool = False,
) -> ViewerCheckResult:
    verification = verify_run(
        run_directory,
        require_complete=require_complete,
        require_live_gpt56=require_live_gpt56,
    )
    errors = list(verification.errors)
    sections: tuple[str, ...] = ()
    viewer_path = run_directory / "viewer.html"

    if verification.passed:
        try:
            file_stat = viewer_path.lstat()
            if not stat.S_ISREG(file_stat.st_mode) or viewer_path.is_symlink():
                errors.append("viewer.html must be a regular non-symlink file")
            elif file_stat.st_size > MAX_VIEWER_BYTES:
                errors.append("viewer.html exceeds the bounded inspection size")
            else:
                text = viewer_path.read_text(encoding="utf-8")
                sections, viewer_errors = inspect_viewer_html(
                    text,
                    require_complete=require_complete or require_live_gpt56,
                )
                errors.extend(viewer_errors)
        except (OSError, UnicodeError) as exc:
            errors.append(f"viewer.html could not be read safely: {type(exc).__name__}")

    return ViewerCheckResult(
        passed=verification.passed and not errors,
        terminal_status=verification.terminal_status,
        verified_artifacts=verification.verified_artifacts,
        verified_audit_entries=verification.verified_audit_entries,
        sections=sections,
        errors=tuple(errors),
        warnings=verification.warnings,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a proof bundle, apply the independent inert-viewer policy, "
            "and confirm the expected offline content sections."
        )
    )
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--require-live-gpt56", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = check_bundle_viewer(
        args.run_directory,
        require_complete=args.require_complete,
        require_live_gpt56=args.require_live_gpt56,
    )
    if args.json_output:
        print(json.dumps(result.public_dict(), indent=2, sort_keys=True))
    else:
        print("VIEWER QA PASS" if result.passed else "VIEWER QA FAIL")
        print(f"Terminal status: {result.terminal_status or 'unknown'}")
        print(f"Sections: {', '.join(result.sections) or 'none'}")
        for warning in result.warnings:
            print(f"Warning: {warning}")
        for error in result.errors:
            print(f"Error: {error}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
