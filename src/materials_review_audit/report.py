from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .utils import write_csv, write_json

REQUIRED_OUTPUTS = [
    "audit_report.md",
    "audit_findings.csv",
    "number_ledger.csv",
    "claim_ledger.csv",
    "claims_to_downgrade.csv",
    "source_data_ledger.csv",
    "missing_files.csv",
    "descriptor_coverage_audit.csv",
    "descriptor_warnings.csv",
    "figure_text_mismatch.csv",
    "conflict_gate_cases.csv",
    "audit_manifest.json",
]


def flatten_findings(*packets: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in packets:
        for f in packet.get("findings", []) or []:
            rows.append(f)
    return rows


def write_report(out_dir: str | Path, findings: list[dict[str, Any]], source_ledger: dict[str, Any], conflict_gate: dict[str, Any]) -> dict[str, Any]:
    out = Path(out_dir)
    counts = Counter(f.get("severity", "") for f in findings)
    category_counts: dict[str, int] = defaultdict(int)
    for f in findings:
        category_counts[str(f.get("category", "uncategorized"))] += 1

    if counts.get("P0", 0):
        readiness = "NOT READY"
        decision_rationale = "At least one P0 finding must be fixed before submission."
    elif counts.get("P1", 0):
        readiness = "CONDITIONALLY READY"
        decision_rationale = "No P0 findings were detected, but P1 findings should be fixed or explicitly justified before submission."
    else:
        readiness = "READY"
        decision_rationale = "No P0/P1 findings were detected by the automated audit. Manual visual and citation checks may still be needed."

    missing = source_ledger.get("missing_files", [])
    manual_visual = [f for f in source_ledger.get("figures", []) if f.get("manual_visual_qa")]

    lines: list[str] = []
    lines.append("# Submission Readiness Report")
    lines.append("")
    lines.append(f"**Decision:** {readiness}")
    lines.append("")
    lines.append(f"**Rationale:** {decision_rationale}")
    lines.append("")
    lines.append("## Severity summary")
    lines.append("")
    lines.append(f"- P0: {counts.get('P0', 0)}")
    lines.append(f"- P1: {counts.get('P1', 0)}")
    lines.append(f"- P2: {counts.get('P2', 0)}")
    lines.append("")
    lines.append("## Category summary")
    lines.append("")
    if category_counts:
        for category, count in sorted(category_counts.items()):
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- No findings detected.")
    lines.append("")
    lines.append("## Fix order")
    lines.append("")
    lines.append("1. Fix P0 numerical, source-data, and figure-text contradictions first.")
    lines.append("2. Fix P1 claim-support and database-coverage issues before final submission.")
    lines.append("3. Use P2 findings for transparency, stale-file cleanup, and wording precision.")
    lines.append("")
    for severity in ("P0", "P1", "P2"):
        lines.append(f"## {severity} findings")
        lines.append("")
        add_findings(lines, [f for f in findings if f.get("severity") == severity])
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
            lines.append(f"- {fig.get('figure_id')}: visually confirm labels, heatmap direction, color scale, source-data linkage, and caption wording.")
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
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- This audit checks consistency and plausibility; it does not replace expert review of the underlying papers.")
    lines.append("- Figure image content still needs manual visual QA when the manifest requests it.")
    lines.append("- Citation adequacy is heuristic unless a separate citation-evidence ledger is supplied.")

    (out / "audit_report.md").write_text("\n".join(lines), encoding="utf-8")
    write_csv(out / "audit_findings.csv", findings)

    manifest = {
        "tool": "materials-review-audit",
        "version": __version__,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "readiness": readiness,
        "severity_counts": dict(counts),
        "category_counts": dict(category_counts),
        "required_outputs": REQUIRED_OUTPUTS,
        "present_outputs": sorted({p.name for p in out.iterdir() if p.is_file()} | {"audit_manifest.json"}),
    }
    write_json(out / "audit_manifest.json", manifest)
    return {"readiness": readiness, "counts": dict(counts), "manifest": manifest}


def add_findings(lines: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        lines.append("- None.")
        return
    for f in rows:
        loc = f.get("location", "")
        lines.append(f"- **{f.get('finding_id')}** `{f.get('category')}` {loc}: {f.get('message')}  ")
        lines.append(f"  Recommended action: {f.get('recommended_action')}")
