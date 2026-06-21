from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .utils import normalize_name, safe_float, write_csv, write_json

DESCRIPTORS = {
    "BET": {"synonyms": ["bet", "sbet", "specific_surface_area", "specific surface area", "surface_area", "surface area", "ssa"], "range": (0, 5000)},
    "d002": {"synonyms": ["d002", "d_002", "interlayer_spacing", "interlayer spacing", "layer_spacing", "layer spacing"], "range_nm": (0.30, 0.50), "range_angstrom": (3.0, 5.0)},
    "ID_IG": {"synonyms": ["id_ig", "id/ig", "i_d_i_g", "i_d/i_g", "raman_id_ig", "raman id/ig", "d_g", "d/g"], "range": (0, 5)},
    "XPS_N": {"synonyms": ["xps_n", "xps n", "n_content", "n content", "n_at", "n at", "n_wt", "n wt"], "range": (0, 50)},
    "XPS_O": {"synonyms": ["xps_o", "xps o", "o_content", "o content", "o_at", "o at", "o_wt", "o wt"], "range": (0, 60)},
    "total_pore_volume": {"synonyms": ["total_pore_volume", "total pore volume", "pore_volume", "pore volume", "vtotal", "v_total"], "range": (0, 10)},
    "micropore_volume": {"synonyms": ["micropore_volume", "micropore volume", "vmicro", "v_micro"], "range": (0, 5)},
    "mass_loading": {"synonyms": ["mass_loading", "mass loading", "loading", "areal_loading", "areal loading"], "range": (0, 100)},
    "electrode_thickness": {"synonyms": ["electrode_thickness", "electrode thickness", "thickness"], "range": (0, 2000)},
    "compacted_density": {"synonyms": ["compacted_density", "compacted density", "tap_density", "tap density", "electrode_density", "electrode density", "density"], "range": (0, 5)},
    "ICE": {"synonyms": ["ice", "initial_coulombic_efficiency", "initial coulombic efficiency", "first_cycle_coulombic_efficiency", "first-cycle coulombic efficiency"], "range": (0, 100)},
    "capacity": {"synonyms": ["capacity", "reversible_capacity", "reversible capacity", "specific_capacity", "specific capacity"], "range": (0, 3000)},
    "capacitance": {"synonyms": ["capacitance", "specific_capacitance", "specific capacitance"], "range": (0, 2000)},
    "current_density": {"synonyms": ["current_density", "current density", "specific_current", "specific current", "a_g", "a g", "a/g"], "range": (0, 200)},
    "voltage_window": {"synonyms": ["voltage_window", "voltage window", "potential_window", "potential window", "voltage_range", "voltage range"], "range": (0, 5)},
}
ENGINEERING = {"mass_loading", "electrode_thickness", "compacted_density"}
COVERAGE_FIELDS = ["descriptor", "column", "n_total", "n_available", "coverage_pct", "status"]
WARNING_FIELDS = ["warning_id", "severity", "descriptor", "row_index", "value", "message"]


def load_database(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    return pd.read_csv(p)


def _matches_column(normalized_col: str, normalized_synonym: str) -> bool:
    if normalized_col == normalized_synonym:
        return True
    col_tokens = set(normalized_col.split("_"))
    syn_tokens = set(normalized_synonym.split("_"))
    if syn_tokens and syn_tokens.issubset(col_tokens):
        return True
    # Allow common unit-decorated columns, e.g. "bet_m2_g" or "specific_capacity_mah_g".
    return len(normalized_synonym) >= 4 and normalized_synonym in normalized_col


def map_columns(columns: list[str]) -> dict[str, str]:
    norm_to_original = {normalize_name(c): c for c in columns}
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for canonical, spec in DESCRIPTORS.items():
        best: str | None = None
        for norm_col, original in norm_to_original.items():
            if original in used:
                continue
            for syn in spec.get("synonyms", []):
                if _matches_column(norm_col, normalize_name(syn)):
                    best = original
                    break
            if best:
                break
        if best:
            mapping[canonical] = best
            used.add(best)
    return mapping


def audit_descriptor_database(database_path: str | Path | None, out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    if not database_path:
        warning = {"warning_id": "DW-0001", "severity": "P1", "descriptor": "database", "row_index": "", "value": "", "message": "no descriptor database provided"}
        packet = {"coverage": [], "warnings": [warning], "canonical_columns": {}, "findings": [{"finding_id": "DA-0001", "severity": "P1", "category": "descriptor_database_audit", "message": warning["message"], "location": "database", "evidence": {}, "recommended_action": "provide descriptor database or explicitly state database audit was not performed"}], "n_rows": 0}
        write_json(Path(state_dir) / "05_descriptor_audit.json", packet)
        write_csv(Path(out_dir) / "descriptor_coverage_audit.csv", [], COVERAGE_FIELDS)
        write_csv(Path(out_dir) / "descriptor_warnings.csv", [warning], WARNING_FIELDS)
        return packet
    df = load_database(database_path)
    mapping = map_columns([str(c) for c in df.columns])
    n = len(df)
    coverage: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    wid = 1

    for canonical, spec in DESCRIPTORS.items():
        col = mapping.get(canonical)
        if col is None:
            coverage.append({"descriptor": canonical, "column": "", "n_total": n, "n_available": 0, "coverage_pct": 0.0, "status": "missing"})
            sev = "P1" if canonical in ENGINEERING else "P2"
            msg = f"descriptor column missing: {canonical}"
            warnings.append({"warning_id": f"DW-{wid:04d}", "severity": sev, "descriptor": canonical, "row_index": "", "value": "", "message": msg})
            findings.append({"finding_id": f"DA-{wid:04d}", "severity": sev, "category": "descriptor_database_audit", "message": msg, "location": str(database_path), "evidence": {"descriptor": canonical}, "recommended_action": "add column, document as unavailable, or state missingness limitation"})
            wid += 1
            continue
        values = df[col]
        available = int(values.notna().sum())
        coverage.append({"descriptor": canonical, "column": col, "n_total": n, "n_available": available, "coverage_pct": round(float(available / n * 100), 2) if n else 0, "status": "available"})
        for idx, value in values.items():
            f = safe_float(value)
            if f is None:
                continue
            ok = True
            range_used = None
            if canonical == "d002":
                nm = spec["range_nm"]
                ag = spec["range_angstrom"]
                ok = (nm[0] <= f <= nm[1]) or (ag[0] <= f <= ag[1])
                range_used = f"{nm} nm or {ag} Å"
            else:
                lo, hi = spec["range"]
                ok = lo <= f <= hi
                range_used = f"{lo}–{hi}"
            if not ok:
                sev = "P0" if canonical in {"ICE", "BET", "d002", "capacity", "capacitance"} else "P1"
                msg = f"{canonical} value {f} outside expected range {range_used}"
                warnings.append({"warning_id": f"DW-{wid:04d}", "severity": sev, "descriptor": canonical, "row_index": int(idx), "value": f, "message": msg})
                findings.append({"finding_id": f"DA-{wid:04d}", "severity": sev, "category": "descriptor_database_audit", "message": msg, "location": f"row {idx}, column {col}", "evidence": {"value": f, "range": range_used}, "recommended_action": "check original paper/source data; correct unit, decimal, or extraction error"})
                wid += 1
    packet = {"coverage": coverage, "warnings": warnings, "canonical_columns": mapping, "findings": findings, "n_rows": n}
    write_json(Path(state_dir) / "05_descriptor_audit.json", packet)
    write_csv(Path(out_dir) / "descriptor_coverage_audit.csv", coverage, COVERAGE_FIELDS)
    write_csv(Path(out_dir) / "descriptor_warnings.csv", warnings, WARNING_FIELDS)
    return packet
