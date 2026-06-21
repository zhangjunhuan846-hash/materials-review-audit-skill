from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import read_csv_rows, write_json

CLAIM_HINTS = re.compile(
    r"(increase|decrease|enhance|improve|reduce|suppress|positive|negative|correlat|trend|significant|dominant|drive|lead|cause|suggest|indicate|higher|lower|提升|降低|正相关|负相关|显著|导致|表明|说明)",
    flags=re.I,
)
NUMBER_HINTS = re.compile(r"\b(n\s*=\s*\d+|\d+(?:\.\d+)?\s*(?:%|mAh|F\s*g|m2|m²|nm|Å|A\s*g))", flags=re.I)
DESCRIPTOR_HINTS = re.compile(r"\b(BET|d002|d_002|ID/IG|I_D/I_G|Raman|XPS|N/O|pore volume|mass loading|thickness|density|ICE|capacity|capacitance)\b", flags=re.I)
FIGURE_HINTS = re.compile(r"Fig(?:ure)?\.?\s*\d+[A-Za-z]?", flags=re.I)


def build_context_pack(inventory: dict[str, Any], reference_numbers_path: str | Path | None, state_dir: str | Path) -> dict[str, Any]:
    paragraphs = inventory.get("paragraphs", [])
    draft_map = {
        "paragraphs": [
            {
                "paragraph_id": p["paragraph_id"],
                "section": p.get("section", ""),
                "approx_tokens": p.get("approx_tokens", 0),
                "has_claim": bool(CLAIM_HINTS.search(p.get("text", ""))),
                "has_number": bool(NUMBER_HINTS.search(p.get("text", ""))),
                "has_descriptor": bool(DESCRIPTOR_HINTS.search(p.get("text", ""))),
                "has_figure": bool(FIGURE_HINTS.search(p.get("text", ""))),
            }
            for p in paragraphs
        ]
    }
    selected = {
        "claim_context": [p for p in paragraphs if CLAIM_HINTS.search(p.get("text", ""))],
        "number_context": [p for p in paragraphs if NUMBER_HINTS.search(p.get("text", ""))],
        "descriptor_context": [p for p in paragraphs if DESCRIPTOR_HINTS.search(p.get("text", ""))],
        "figure_context": [p for p in paragraphs if FIGURE_HINTS.search(p.get("text", ""))],
    }
    reference_numbers = read_csv_rows(reference_numbers_path) if reference_numbers_path else []
    evidence_pack = {
        "figures": inventory.get("figures", []),
        "source_data_files": inventory.get("source_data_files", []),
        "database_path": inventory.get("database_path"),
        "reference_numbers": reference_numbers,
        "token_saving_note": "Agents should read selected local context and evidence packets, not the full manuscript.",
    }
    state = Path(state_dir)
    write_json(state / "draft_map.json", draft_map)
    write_json(state / "selected_context.json", selected)
    write_json(state / "evidence_pack.json", evidence_pack)
    return {"draft_map": draft_map, "selected_context": selected, "evidence_pack": evidence_pack}
