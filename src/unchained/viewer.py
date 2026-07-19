"""Deterministic, self-contained, network-inert proof-bundle viewer."""

# The embedded HTML/CSS intentionally keeps one source line per rendered rule.
# ruff: noqa: E501

from __future__ import annotations

import html
from typing import Any

from .models import EvidenceProfile

_TIMELINE_EVENTS = {
    "profile.completed": "Profile and route",
    "opening.completed": "Opening tools",
    "investigator.done": "Literal DONE",
    "investigator.finished": "Forced serialization",
    "judge.completed": "Fresh judge",
    "report.completed": "Report draft and render",
    "custody.final.completed": "Final custody check",
}


def render_viewer_html(
    *,
    run_id: str,
    status: str,
    profile: EvidenceProfile | None,
    summary: dict[str, Any],
    report_markdown: str,
    audit_entries: list[dict[str, Any]],
) -> str:
    """Return one static HTML document with no scripts or external resources."""

    evidence_rows = (
        "".join(
            "<tr>"
            f"<td><code>{_escape(item.evidence_id)}</code></td>"
            f"<td>{_escape(item.kind)}</td>"
            f"<td>{item.size:,}</td>"
            f"<td>{_escape(item.health)}</td>"
            f"<td><code>{_escape(item.sha256)}</code></td>"
            "</tr>"
            for item in (() if profile is None else profile.items)
        )
        or '<tr><td colspan="5" class="muted">No evidence profile was completed.</td></tr>'
    )

    timeline_rows = (
        "".join(
            "<li>"
            f"<span>{_escape(_TIMELINE_EVENTS[str(entry.get('event_type'))])}</span>"
            f"<time>{_elapsed(entry.get('elapsed_ms'))}</time>"
            "</li>"
            for entry in audit_entries
            if entry.get("event_type") in _TIMELINE_EVENTS
        )
        or '<li><span class="muted">No completed phase events.</span></li>'
    )

    tool_rows = (
        "".join(
            _tool_row(entry.get("payload"))
            for entry in audit_entries
            if entry.get("event_type") == "tool.completed"
        )
        or '<tr><td colspan="5" class="muted">No tool completions were recorded.</td></tr>'
    )

    custody = _custody_card(audit_entries)
    route = "not established" if profile is None else f"{profile.os} / {profile.shape}"
    capability = "not established" if profile is None else profile.capability_label
    status_class = (
        status.casefold() if status in {"COMPLETE", "PARTIAL", "INVALID", "FATAL"} else "fatal"
    )
    reason = summary.get("reason") or "No terminal reason was recorded."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; media-src 'none'; connect-src 'none'; script-src 'none'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'none'">
  <title>Unchained proof — {_escape(run_id)}</title>
  <style>
    :root {{ color-scheme: dark; --bg:#07111f; --panel:#0d1b2d; --line:#233852; --ink:#e8f0fb; --muted:#9db0c8; --cyan:#56d7e8; --green:#55d692; --amber:#f2be63; --red:#ff7b84; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:radial-gradient(circle at top right,#112b42 0,#07111f 42rem); color:var(--ink); font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }}
    main {{ width:min(1180px,calc(100% - 32px)); margin:0 auto; padding:40px 0 72px; }}
    header {{ display:flex; gap:24px; align-items:flex-start; justify-content:space-between; margin-bottom:24px; }}
    h1 {{ margin:0; font-size:clamp(28px,5vw,52px); letter-spacing:-.04em; }}
    h2 {{ margin:0 0 14px; font-size:18px; }}
    p {{ margin:.35rem 0; }}
    .eyebrow {{ color:var(--cyan); text-transform:uppercase; letter-spacing:.14em; font-weight:700; font-size:12px; }}
    .badge {{ border:1px solid currentColor; border-radius:999px; padding:8px 14px; font-weight:800; letter-spacing:.08em; }}
    .complete {{ color:var(--green); }} .partial {{ color:var(--amber); }} .invalid,.fatal {{ color:var(--red); }}
    .grid {{ display:grid; grid-template-columns:repeat(12,1fr); gap:16px; }}
    .card {{ grid-column:span 6; background:var(--panel); background:color-mix(in srgb,var(--panel) 94%,transparent); border:1px solid var(--line); border-radius:16px; padding:20px; box-shadow:0 16px 48px #0004; overflow:hidden; }}
    .wide {{ grid-column:1/-1; }} .third {{ grid-column:span 4; }}
    .label {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.09em; }}
    .value {{ font-size:18px; font-weight:700; overflow-wrap:anywhere; }}
    code {{ color:#b9f3fb; font:12px/1.45 ui-monospace,SFMono-Regular,Consolas,monospace; overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; }} th,td {{ text-align:left; padding:10px 9px; border-bottom:1px solid var(--line); vertical-align:top; }} th {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.06em; }}
    ol {{ list-style:none; margin:0; padding:0; }} ol li {{ display:flex; justify-content:space-between; gap:16px; padding:8px 0; border-bottom:1px solid var(--line); }} time,.muted {{ color:var(--muted); }}
    details {{ border-top:1px solid var(--line); padding-top:14px; }} summary {{ cursor:pointer; color:var(--cyan); font-weight:700; }}
    pre {{ white-space:pre-wrap; overflow-wrap:anywhere; padding:16px; background:#06101c; border:1px solid var(--line); border-radius:12px; color:#dbe8f7; max-height:70vh; overflow:auto; }}
    .notice {{ border-left:3px solid var(--amber); padding-left:12px; color:var(--muted); }}
    @media (max-width:800px) {{ header {{ display:block; }} .badge {{ display:inline-block; margin-top:16px; }} .card,.third {{ grid-column:1/-1; }} main {{ width:min(100% - 20px,1180px); padding-top:24px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div><div class="eyebrow">Recorded local proof bundle · verify before trust</div><h1>Unchained</h1><p><code>{_escape(run_id)}</code></p></div>
    <div class="badge {status_class}">RECORDED {_escape(status)}</div>
  </header>
  <section class="grid" aria-label="Run overview">
    <article class="card third"><div class="label">Evidence route</div><div class="value">{_escape(route)}</div></article>
    <article class="card third"><div class="label">Capability</div><div class="value">{_escape(capability)}</div></article>
    <article class="card third"><div class="label">Exit code</div><div class="value">{_escape(summary.get("exit_code"))}</div></article>
    <article class="card"><h2>Protocol timeline</h2><ol>{timeline_rows}</ol></article>
    <article class="card"><h2>Custody receipt</h2>{custody}<p class="notice">This inert page displays recorded receipts and cannot verify itself. Open it through <code>sentinel view &lt;run&gt;</code> to validate the manifest first. An offline recipient does not rehash the original evidence or authenticate provider-issued IDs.</p></article>
    <article class="card wide"><h2>Evidence inventory</h2><table><thead><tr><th>ID</th><th>Kind</th><th>Bytes</th><th>Health</th><th>SHA-256</th></tr></thead><tbody>{evidence_rows}</tbody></table></article>
    <article class="card wide"><h2>Typed tool receipts</h2><table><thead><tr><th>Call</th><th>Tool</th><th>Status</th><th>Duration</th><th>Evidence binding</th></tr></thead><tbody>{tool_rows}</tbody></table></article>
    <article class="card wide"><h2>Terminal context</h2><p>{_escape(reason)}</p></article>
    <article class="card wide"><h2>Analyst report</h2><details open><summary>Show deterministic Markdown artifact</summary><pre>{_escape(report_markdown)}</pre></details></article>
  </section>
</main>
</body>
</html>
"""


def _tool_row(raw: Any) -> str:
    if not isinstance(raw, dict):
        return ""
    references = raw.get("evidence_refs")
    if isinstance(references, list):
        binding = ", ".join(
            f"{value.get('evidence_id')}:{str(value.get('sha256') or '')[:12]}"
            for value in references
            if isinstance(value, dict)
        )
    else:
        binding = "unrecorded"
    return (
        "<tr>"
        f"<td><code>{_escape(raw.get('tool_call_id'))}</code></td>"
        f"<td>{_escape(raw.get('tool_name'))}</td>"
        f"<td>{_escape(raw.get('status'))}</td>"
        f"<td>{_escape(raw.get('duration_ms'))} ms</td>"
        f"<td><code>{_escape(binding or 'none')}</code></td>"
        "</tr>"
    )


def _custody_card(entries: list[dict[str, Any]]) -> str:
    initial = next(
        (
            entry.get("payload")
            for entry in entries
            if entry.get("event_type") == "custody.initial.completed"
        ),
        None,
    )
    final = next(
        (
            entry.get("payload")
            for entry in entries
            if entry.get("event_type") == "custody.final.completed"
        ),
        None,
    )
    initial_hashes = initial.get("hashes") if isinstance(initial, dict) else None
    final_hashes = final.get("hashes") if isinstance(final, dict) else None
    matched = bool(
        isinstance(final, dict)
        and final.get("match") is True
        and isinstance(initial_hashes, dict)
        and initial_hashes == final_hashes
    )
    label = "MATCH" if matched else "NOT ESTABLISHED"
    css = "complete" if matched else "partial"
    count = len(initial_hashes) if isinstance(initial_hashes, dict) else 0
    return f'<p class="value {css}">{label}</p><p>{count} evidence digest(s) recorded.</p>'


def _elapsed(value: Any) -> str:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return f"{value / 1000:.2f}s"
    return "unknown"


def _escape(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)
