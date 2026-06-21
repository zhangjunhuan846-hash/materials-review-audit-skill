from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import list_files, write_csv, write_json

QUANT_TYPES = {"heatmap", "correlation_heatmap", "bar", "line", "scatter", "database_plot", "statistical_plot", "box", "violin"}


def build_source_data_ledger(figures: list[dict[str, Any]], source_data_dir: str | Path | None, out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    source_files = list_files(source_data_dir, ("*.csv", "*.xlsx", "*.xls")) if source_data_dir else []
    source_set = set(source_files)
    rows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    expected_all: set[str] = set()
    findings: list[dict[str, Any]] = []
    fid = 1
    for fig in figures:
        figure_id = fig.get("figure_id") or fig.get("id") or "unknown"
        ftype = str(fig.get("figure_type", "")).lower()
        quantitative = bool(fig.get("quantitative", False)) or ftype in QUANT_TYPES
        required = bool(fig.get("source_data_required", quantitative))
        expected = fig.get("expected_source_files", []) or fig.get("source_files", []) or []
        if isinstance(expected, str):
            expected = [expected]
        expected_all.update(expected)
        missing_files = [f for f in expected if f not in source_set]
        status = "ok"
        severity = ""
        if required and not expected:
            status = "missing_manifest_entry"
            severity = "P0" if quantitative else "P1"
        elif required and missing_files:
            status = "missing_source_data"
            severity = "P0" if quantitative else "P1"
        row = {
            "figure_id": figure_id,
            "title": fig.get("title", ""),
            "figure_type": fig.get("figure_type", ""),
            "quantitative": quantitative,
            "source_data_required": required,
            "expected_source_files": expected,
            "missing_source_files": missing_files,
            "manual_visual_qa": bool(fig.get("manual_visual_qa", False)),
            "status": status,
            "severity": severity,
        }
        rows.append(row)
        if missing_files or status == "missing_manifest_entry":
            missing.append(row)
            findings.append({
                "finding_id": f"SD-{fid:04d}",
                "severity": severity or "P1",
                "category": "source_data_ledger",
                "message": f"{figure_id} lacks required source-data support",
                "location": figure_id,
                "evidence": row,
                "recommended_action": "add matching source_data file or update figures_manifest.json",
            })
            fid += 1
    orphan_files = sorted(source_set - expected_all)
    orphan_rows = [{"source_file": f, "severity": "P2", "message": "source-data file is present but not referenced by figures_manifest.json"} for f in orphan_files]
    for row in orphan_rows:
        findings.append({
            "finding_id": f"SD-{fid:04d}",
            "severity": "P2",
            "category": "source_data_ledger",
            "message": row["message"],
            "location": row["source_file"],
            "evidence": row,
            "recommended_action": "link the file in figures_manifest.json or remove stale source-data file",
        })
        fid += 1
    packet = {"figures": rows, "missing_files": missing, "orphan_files": orphan_rows, "findings": findings}
    write_json(Path(state_dir) / "04_source_data_ledger.json", packet)
    write_csv(Path(out_dir) / "source_data_ledger.csv", rows)
    write_csv(Path(out_dir) / "missing_files.csv", missing + orphan_rows)
    return packet
