"""Fallback reports must treat diagnostics as hostile, inert text."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from types import SimpleNamespace

from markdown_it import MarkdownIt

from unchained.agent import UnchainedAgent, _sanitize_markdown, defang_untrusted_inline
from unchained.cli import _fatal_report, _invalid_report
from unchained.models import InvestigationState

MALICIOUS_DIAGNOSTIC = (
    "parser failed\n## FORGED FINDING\n"
    "![beacon](https://attacker.invalid/pixel)\n"
    "<script>alert(1)</script>\n```\nforged fence"
)


class _RenderedHtmlAudit(HTMLParser):
    """Collect active elements and URL-bearing attributes from rendered Markdown."""

    ACTIVE_TAGS = {
        "a",
        "audio",
        "button",
        "embed",
        "form",
        "iframe",
        "img",
        "input",
        "link",
        "meta",
        "object",
        "script",
        "source",
        "style",
        "svg",
        "video",
    }
    ACTIVE_ATTRIBUTES = {
        "action",
        "data",
        "formaction",
        "href",
        "poster",
        "src",
        "srcset",
        "style",
    }

    def __init__(self) -> None:
        super().__init__()
        self.active_tags: list[str] = []
        self.active_attributes: list[tuple[str, str]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in self.ACTIVE_TAGS:
            self.active_tags.append(normalized_tag)
        for name, value in attrs:
            normalized_name = name.casefold()
            if normalized_name in self.ACTIVE_ATTRIBUTES or normalized_name.startswith("on"):
                self.active_attributes.append((normalized_name, value or ""))

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)


def _render_and_audit(markdown: str) -> tuple[str, _RenderedHtmlAudit]:
    rendered_html = MarkdownIt("commonmark", {"html": True}).render(markdown)
    audit = _RenderedHtmlAudit()
    audit.feed(rendered_html)
    return rendered_html, audit


def _assert_inert(report: str) -> None:
    assert "\n## FORGED FINDING" not in report
    assert "https://attacker.invalid" not in report
    assert "<script>" not in report
    assert "\n```\nforged fence" not in report
    assert len(re.findall(r"(?m)^# Unchained DFIR Report", report)) == 1


def test_inline_defanger_escapes_structure_controls_and_active_content() -> None:
    rendered = defang_untrusted_inline(MALICIOUS_DIAGNOSTIC)

    assert "\n" not in rendered
    assert "FORGED FINDING" in rendered
    assert "![" not in rendered
    assert "https://attacker.invalid" not in rendered
    assert "blocked" not in rendered  # no javascript URI was supplied
    assert "<script>" not in rendered


def test_cli_fallback_reports_defang_hostile_diagnostics() -> None:
    _assert_inert(_fatal_report(MALICIOUS_DIAGNOSTIC))
    _assert_inert(_invalid_report(MALICIOUS_DIAGNOSTIC))


def test_agent_partial_report_defangs_hostile_protocol_reason() -> None:
    route = SimpleNamespace(os="windows", shape="memory-only")
    report = UnchainedAgent._protocol_partial_report(  # noqa: SLF001 - safety regression
        route,  # type: ignore[arg-type] - only deterministic route fields are consumed
        InvestigationState(),
        MALICIOUS_DIAGNOSTIC,
    )

    _assert_inert(report)


def test_complete_report_sanitizer_removes_all_active_link_and_image_forms() -> None:
    hostile = """![inline](data:image/svg+xml,bad)
![reference][pixel]
[pixel]: https://attacker.invalid/pixel
[local file](file:///etc/passwd)
[script](javascript:alert(1))
"""

    rendered = _sanitize_markdown(hostile)

    assert "![" not in rendered
    assert "https://" not in rendered
    assert "data:" not in rendered
    assert "file:" not in rendered
    assert "javascript:" not in rendered


def test_complete_report_sanitizer_is_inert_after_commonmark_rendering() -> None:
    hostile = r"""## Narrative
![a\]](//attacker.invalid/pixel)
![nested [label]](https://attacker.invalid/a_(b).svg "title")
![reference][pixel]
[pixel]: https://attacker.invalid/reference.svg
[inline](javascript:alert(1))
[encoded](&#x6a;avascript&#58;alert(1))
[file](file:///etc/passwd)
<https://attacker.invalid/autolink>
https://attacker.invalid/bare
www.attacker.invalid/fuzzy
operator@attacker.invalid
<img src="//attacker.invalid/raw" onerror="alert(1)">
&#60;script&#62;alert(1)&#60;/script&#62;
"""

    sanitized = _sanitize_markdown(hostile)
    rendered_html, audit = _render_and_audit(sanitized)

    assert audit.active_tags == []
    assert audit.active_attributes == []
    assert "//attacker.invalid" not in rendered_html
    assert "https://attacker.invalid" not in rendered_html
    assert "www.attacker.invalid" not in rendered_html
    assert "operator@attacker.invalid" not in rendered_html
    assert "javascript:" not in rendered_html.casefold()
    assert "file:" not in rendered_html.casefold()


def test_complete_report_sanitizer_preserves_visible_citations_without_links() -> None:
    sanitized = _sanitize_markdown("## Findings\n\n| Finding | Tool |\n|---|---|\n| F001 | [t17] |")
    rendered_html, audit = _render_and_audit(sanitized)

    assert "[t17]" in rendered_html
    assert audit.active_tags == []
    assert audit.active_attributes == []
