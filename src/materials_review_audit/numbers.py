from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import read_csv_rows, safe_float, write_csv, write_json

NUMBER_RE = re.compile(r"(?P<label>LIB|SIB|SC|aqueous\s+SC|sample|record|records|n)\D{0,40}(?P<value>\d+(?:\.\d+)?)", re.I)


def build_number_ledger(selected_context: dict[str, Any], reference_numbers_path: str | Path | None, out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    nid = 1
    for p in selected_context.get("number_context", []):
        text = p.get("text", "")
        for m in NUMBER_RE.finditer(text):
            rows.append({"number_id": f"N-{nid:04d}", "paragraph_id": p.get("paragraph_id"), "section": p.get("section"), "label_hint": m.group("label"), "value": m.group("value"), "context": text[:300]})
            nid += 1
    refs = read_csv_rows(reference_numbers_path) if reference_numbers_path else []
    # Lightweight exact-match check: if the label appears in text but expected value does not.
    fid = 1
    full_text = "\n".join(p.get("text", "") for p in selected_context.get("number_context", []))
    for r in refs:
        label = str(r.get("label", ""))
        expected = safe_float(r.get("expected_value"))
        if not label or expected is None:
            continue
        loose_label = label.split("_")[0]
        if loose_label and loose_label.lower() in full_text.lower() and str(int(expected) if expected.is_integer() else expected) not in full_text:
            findings.append({"finding_id": f"NL-{fid:04d}", "severity": "P0", "category": "number_ledger", "message": f"reference value for {label} not found in number-bearing manuscript context", "location": "manuscript", "evidence": r, "recommended_action": "check manuscript, SI, figure captions, and database count consistency"})
            fid += 1
    packet = {"numbers": rows, "reference_numbers": refs, "findings": findings}
    write_json(Path(state_dir) / "02_number_ledger.json", packet)
    write_csv(Path(out_dir) / "number_ledger.csv", rows)
    return packet
