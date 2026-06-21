from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .utils import normalize_name, safe_float, write_csv, write_json

DESCRIPTORS = {
    "BET": {"synonyms": ["bet", "sbet", "specific_surface_area", "surface_area", "ssa"], "range": (0, 5000)},
    "d002": {"synonyms": ["d002", "d_002", "interlayer_spacing", "layer_spacing"], "range_nm": (0.30, 0.50), "range_angstrom": (3.0, 5.0)},
    "ID_IG": {"synonyms": ["id_ig", "i_d_i_g", "raman_id_ig", "d_g"], "range": (0, 5)},
    "XPS_N": {"synonyms": ["n", "n_content", "xps_n", "n_at", "n_wt"], "range": (0, 50)},
    "XPS_O": {"synonyms": ["o", "o_content", "xps_o", "o_at", "o_wt"], "range": (0, 60)},
    "total_pore_volume": {"synonyms": ["total_pore_volume", "pore_volume", "vtotal", "v_total"], "range": (0, 10)},
    "micropore_volume": {"synonyms": ["micropore_volume", "vmicro", "v_micro"], "range": (0, 5)},
    "mass_loading": {"synonyms": ["mass_loading", "loading", "areal_loading"], "range": (0, 100)},
    "electrode_thickness": {"synonyms": ["electrode_thickness", "thickness"], "range": (0, 2000)},
    "compacted_density": {"synonyms": ["compacted_density", "tap_density", "electrode_density", "density"], "range": (0, 5)},
    "ICE": {"synonyms": ["ice", "initial_coulombic_efficiency", "first_cycle_coulombic_efficiency"], "range": (0, 100)},
    "capacity": {"synonyms": ["capacity", "reversible_capacity", "specific_capacity"], "range": (0, 3000)},
    "capacitance": {"synonyms": ["capacitance", "specific_capacitance"], "range": (0, 2000)},
    "current_density": {"synonyms": ["current_density", "specific_current", "a_g"], "range": (0, 200)},
    "voltage_window": {"synonyms": ["voltage_window", "potential_window", "voltage_range"], "range": (0, 5)},
}
ENGINEERING = {"mass_loading", "electrode_thickness", "compacted_density"}


def load_database(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    return pd.read_csv(p)


def map_columns(columns: list[str]) -> dict[str, str]:
    norm_to_original = {normalize_name(c): c for c in columns}
    mapping: dict[str, str] = {}
    for canonical, spec in DESCRIPTORS.items():
        for syn in spec.get("synonyms", []):
            ns = normalize_name(syn)
            if ns in norm_to_original:
                mapping[canonical] = norm_to_original[ns]
                break
    return mapping


def audit_descriptor_database(database_path: str | Path | None, out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    if not database_path:
        packet = {"coverage": [], "warnings": [{"severity": "P1", "message": "no descriptor database provided"}], "canonical_columns": {}, "findings": []}
        write_json(Path(state_dir) / "05_descriptor_audit.json", packet)
        return packet
    df = load_database(database_path)
    mapping = map_columns(list(df.columns))
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
        available = values.notna().sum()
        coverage.append({"descriptor": canonical, "column": col, "n_total": n, "n_available": int(available), "coverage_pct": round(float(available / n * 100), 2) if n else 0, "status": "available"})
        for idx, value in values.items():
            f = safe_float(value)
            if f is None:
                continue
            ok = True
            range_used = None
            if canonical == "d002":
                # Accept either nm or angstrom style ranges.
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
    write_csv(Path(out_dir) / "descriptor_coverage_audit.csv", coverage)
    write_csv(Path(out_dir) / "descriptor_warnings.csv", warnings)
    return packet
