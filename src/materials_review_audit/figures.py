from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from .utils import normalize_name, safe_float, write_csv, write_json

POS = re.compile(r"(positive|positively|increase|increases|increased|higher|improve|improved|enhance|enhanced|正相关|增加|提高|提升)", re.I)
NEG = re.compile(r"(negative|negatively|decrease|decreases|decreased|lower|reduce|reduced|suppress|suppressed|负相关|降低|减少|抑制)", re.I)
STRONG = re.compile(r"(significant|significantly|markedly|clearly|obvious|substantial|显著|明显)", re.I)
DESCRIPTORS = ["BET", "d002", "ID/IG", "ICE", "capacity", "capacitance", "N", "O", "pore volume", "mass loading"]


def detect_text_direction(text: str) -> str:
    if POS.search(text) and not NEG.search(text):
        return "positive"
    if NEG.search(text) and not POS.search(text):
        return "negative"
    return "unclear"


def load_direction_evidence(source_data_dir: str | Path | None, source_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not source_data_dir:
        return rows
    base = Path(source_data_dir)
    for fig in source_ledger.get("figures", []):
        for fname in fig.get("expected_source_files", []) or []:
            p = base / fname
            if not p.exists() or p.suffix.lower() != ".csv":
                continue
            try:
                df = pd.read_csv(p)
            except Exception:
                continue
            cols = {normalize_name(c): c for c in df.columns}
            rho_col = None
            for key in ["rho", "spearman_rho", "correlation", "r"]:
                if key in cols:
                    rho_col = cols[key]
                    break
            if rho_col is None:
                continue
            desc_col = cols.get("descriptor") or cols.get("x") or cols.get("feature")
            target_col = cols.get("target") or cols.get("y") or cols.get("property")
            for _, r in df.iterrows():
                rho = safe_float(r.get(rho_col))
                if rho is None:
                    continue
                rows.append({
                    "figure_id": fig.get("figure_id"),
                    "source_file": fname,
                    "descriptor": str(r.get(desc_col, "")) if desc_col else "",
                    "target": str(r.get(target_col, "")) if target_col else "",
                    "rho": rho,
                    "data_direction": "positive" if rho > 0.1 else "negative" if rho < -0.1 else "near_zero",
                })
    return rows


def audit_figure_text(claim_ledger: dict[str, Any], source_ledger: dict[str, Any], source_data_dir: str | Path | None, out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    evidence = load_direction_evidence(source_data_dir, source_ledger)
    mismatches: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    mid = 1
    for claim in claim_ledger.get("claims", []):
        text = claim.get("claim_text", "")
        direction = detect_text_direction(text)
        if direction == "unclear":
            continue
        text_norm = text.lower()
        for ev in evidence:
            desc = str(ev.get("descriptor", ""))
            target = str(ev.get("target", ""))
            if desc and desc.lower() not in text_norm:
                # Special handling for ID/IG slash variants.
                if normalize_name(desc) not in normalize_name(text):
                    continue
            if target and target.lower() not in text_norm and normalize_name(target) not in normalize_name(text):
                # target absence is tolerated for broad figure-level statements.
                pass
            data_dir = ev.get("data_direction")
            contradiction = (direction == "positive" and data_dir == "negative") or (direction == "negative" and data_dir == "positive")
            unsupported_strong = bool(STRONG.search(text)) and data_dir == "near_zero"
            if contradiction or unsupported_strong:
                sev = "P0" if contradiction else "P1"
                msg = "text direction contradicts source-data direction" if contradiction else "strong text wording is unsupported by near-zero source-data direction"
                row = {
                    "mismatch_id": f"FT-{mid:04d}",
                    "severity": sev,
                    "claim_id": claim.get("claim_id"),
                    "figure_id": ev.get("figure_id"),
                    "source_file": ev.get("source_file"),
                    "descriptor": desc,
                    "target": target,
                    "text_direction": direction,
                    "data_direction": data_dir,
                    "rho": ev.get("rho"),
                    "claim_text": text,
                    "message": msg,
                }
                mismatches.append(row)
                findings.append({"finding_id": f"FT-{mid:04d}", "severity": sev, "category": "figure_text_consistency", "message": msg, "location": f"{claim.get('paragraph_id')} / {ev.get('figure_id')}", "evidence": row, "recommended_action": "revise text direction or correct source data/figure"})
                mid += 1
    packet = {"direction_evidence": evidence, "mismatches": mismatches, "findings": findings}
    write_json(Path(state_dir) / "06_figure_text_audit.json", packet)
    write_csv(Path(out_dir) / "figure_text_mismatch.csv", mismatches)
    return packet
