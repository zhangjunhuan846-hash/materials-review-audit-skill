from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .utils import write_csv


def flatten_findings(*packets: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in packets:
        for f in packet.get("findings", []) or []:
            rows.append(f)
    return rows


def write_report(out_dir: str | Path, findings: list[dict[str, Any]], source_ledger: dict[str, Any], conflict_gate: dict[str, Any]) -> dict[str, Any]:
    out = Path(out_dir)
    counts = Counter(f.get("severity", "") for f in findings)
    if counts.get("P0", 0):
        readiness = "NOT READY"
    elif counts.get("P1", 0):
        readiness = "CONDITIONALLY READY"
    else:
        readiness = "READY"
    missing = source_ledger.get("missing_files", [])
    manual_visual = [f for f in source_ledger.get("figures", []) if f.get("manual_visual_qa")]
    lines = []
    lines.append("# Submission Readiness Report")
    lines.append("")
    lines.append(f"**Decision:** {readiness}")
    lines.append("")
    lines.append("## Severity summary")
    lines.append("")
    lines.append(f"- P0: {counts.get('P0', 0)}")
    lines.append(f"- P1: {counts.get('P1', 0)}")
    lines.append(f"- P2: {counts.get('P2', 0)}")
    lines.append("")
    lines.append("## P0 findings")
    lines.append("")
    add_findings(lines, [f for f in findings if f.get("severity") == "P0"])
    lines.append("")
    lines.append("## P1 findings")
    lines.append("")
    add_findings(lines, [f for f in findings if f.get("severity") == "P1"])
    lines.append("")
    lines.append("## P2 findings")
    lines.append("")
    add_findings(lines, [f for f in findings if f.get("severity") == "P2"])
    lines.append("")
    lines.append("## Missing files")
    lines.append("")
    if missing:
        for item in missing:
            lines.append(f"- {item.get('figure_id', item.get('source_file', 'unknown'))}: {item.get('missing_source_files', item.get('message', 'missing'))}")
    else:
        lines.append("- None detected by the source-data ledger.")
    lines.append("")
    lines.append("## Manual visual QA checklist")
    lines.append("")
    if manual_visual:
        for fig in manual_visual:
            lines.append(f"- {fig.get('figure_id')}: visually confirm labels, heatmap direction, color scale, and caption wording.")
    else:
        lines.append("- No figure was marked as requiring manual visual QA in the manifest.")
    lines.append("")
    lines.append("## Conflict Gate cases")
    lines.append("")
    cases = conflict_gate.get("cases", [])
    if cases:
        for c in cases:
            lines.append(f"- {c.get('case_id')} / {c.get('finding_id')}: final severity {c.get('final_severity')}; {c.get('recommended_action')}")
    else:
        lines.append("- No P0/P1 case entered Conflict Gate.")
    (out / "audit_report.md").write_text("\n".join(lines), encoding="utf-8")
    write_csv(out / "audit_findings.csv", findings)
    return {"readiness": readiness, "counts": dict(counts)}


def add_findings(lines: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        lines.append("- None.")
        return
    for f in rows:
        loc = f.get("location", "")
        lines.append(f"- **{f.get('finding_id')}** `{f.get('category')}` {loc}: {f.get('message')}  ")
        lines.append(f"  Recommended action: {f.get('recommended_action')}")
