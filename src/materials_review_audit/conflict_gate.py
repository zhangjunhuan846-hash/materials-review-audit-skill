from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import write_csv, write_json

CASE_FIELDS = ["case_id", "finding_id", "initial_severity", "category", "advocate", "skeptic", "arbiter", "final_severity", "recommended_action"]


def build_conflict_gate(findings: list[dict[str, Any]], out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    high = [f for f in findings if f.get("severity") in {"P0", "P1"}]
    cases: list[dict[str, Any]] = []
    for i, f in enumerate(high, start=1):
        category = f.get("category", "")
        severity = f.get("severity", "P1")
        case = {
            "case_id": f"CG-{i:04d}",
            "finding_id": f.get("finding_id", ""),
            "initial_severity": severity,
            "category": category,
            "advocate": advocate_text(f),
            "skeptic": skeptic_text(f),
            "arbiter": arbiter_text(f),
            "final_severity": severity,
            "recommended_action": f.get("recommended_action", "manual expert review"),
        }
        cases.append(case)
    packet = {"cases": cases}
    write_json(Path(state_dir) / "07_conflict_gate.json", packet)
    write_csv(Path(out_dir) / "conflict_gate_cases.csv", cases, CASE_FIELDS)
    return packet


def advocate_text(f: dict[str, Any]) -> str:
    return f"The finding should be retained because it affects {f.get('category')} and is supported by the recorded evidence: {f.get('message')}."


def skeptic_text(f: dict[str, Any]) -> str:
    return "Check whether the issue is caused by naming mismatch, missing manifest metadata, unit convention, or intentionally qualitative text before revising the manuscript."


def arbiter_text(f: dict[str, Any]) -> str:
    if f.get("severity") == "P0":
        return "Keep as P0 until the source file, number, descriptor value, or figure-text direction is corrected and rerun."
    return "Keep as P1 unless the author provides direct citation/source-data evidence or downgrades the claim wording."
