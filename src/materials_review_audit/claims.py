from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import split_sentences, write_csv, write_json

CLAIM_HINTS = re.compile(
    r"(increase|decrease|enhance|improve|reduce|suppress|positive|negative|correlat|trend|significant|dominant|drive|lead|cause|suggest|indicate|higher|lower|提升|降低|正相关|负相关|显著|导致|表明|说明)",
    flags=re.I,
)
CAUSAL_HINTS = re.compile(r"(cause|causes|caused|lead to|leads to|drives?|due to|because|resulting in|therefore|mechanism|导致|驱动|归因于|由于|因此)", flags=re.I)
TREND_HINTS = re.compile(r"(positive|negative|correlat|trend|association|rho|spearman|正相关|负相关|趋势|相关)", flags=re.I)
CITATION_HINTS = re.compile(r"(\[[0-9,\-–\s]+\]|\([A-Z][A-Za-z]+\s+et\s+al\.,?\s+\d{4}\))")
SOURCE_HINTS = re.compile(r"(Fig(?:ure)?\.?\s*\d+|Table\s*\d+|source data|database|Fig\.)", flags=re.I)
LOW_N_HINTS = re.compile(r"\bn\s*[=<]\s*(\d+)\b", flags=re.I)
CLAIM_FIELDS = ["claim_id", "paragraph_id", "section", "claim_text", "needs_citation", "needs_source_data", "causal_overclaim", "trend_or_association_claim", "low_n_caution", "severity", "reasons", "recommended_action"]
FINDING_FIELDS = ["finding_id", "severity", "category", "message", "location", "evidence", "recommended_action"]


def build_claim_ledger(selected_context: dict[str, Any], out_dir: str | Path, state_dir: str | Path) -> dict[str, Any]:
    claims: list[dict[str, Any]] = []
    finding_rows: list[dict[str, Any]] = []
    cid = 1
    for p in selected_context.get("claim_context", []):
        for sent in split_sentences(p.get("text", "")):
            if not CLAIM_HINTS.search(sent):
                continue
            needs_citation = not bool(CITATION_HINTS.search(sent))
            needs_source_data = bool(TREND_HINTS.search(sent) or SOURCE_HINTS.search(sent)) and not bool(SOURCE_HINTS.search(sent))
            over_causal = bool(CAUSAL_HINTS.search(sent) and TREND_HINTS.search(sent))
            low_n = False
            m = LOW_N_HINTS.search(sent)
            if m:
                try:
                    low_n = int(m.group(1)) < 10
                except Exception:
                    low_n = False
            severity = "P2"
            reasons = []
            if needs_citation:
                severity = "P1"
                reasons.append("needs citation")
            if needs_source_data:
                severity = "P1"
                reasons.append("needs source data")
            if over_causal:
                severity = "P1"
                reasons.append("possible causal overclaim from association/trend wording")
            if low_n:
                reasons.append("low-n caution")
            claim = {
                "claim_id": f"C-{cid:04d}",
                "paragraph_id": p.get("paragraph_id"),
                "section": p.get("section"),
                "claim_text": sent,
                "needs_citation": needs_citation,
                "needs_source_data": needs_source_data,
                "causal_overclaim": over_causal,
                "trend_or_association_claim": bool(TREND_HINTS.search(sent)),
                "low_n_caution": low_n,
                "severity": severity if reasons else "",
                "reasons": reasons,
                "recommended_action": recommend_action(needs_citation, needs_source_data, over_causal, low_n),
            }
            claims.append(claim)
            if reasons:
                finding_rows.append({
                    "finding_id": f"CL-{cid:04d}",
                    "severity": severity,
                    "category": "claim_ledger",
                    "message": "; ".join(reasons),
                    "location": p.get("paragraph_id"),
                    "evidence": sent,
                    "recommended_action": claim["recommended_action"],
                })
            cid += 1
    packet = {"claims": claims, "findings": finding_rows}
    write_json(Path(state_dir) / "03_claim_ledger.json", packet)
    write_csv(Path(out_dir) / "claim_ledger.csv", claims, CLAIM_FIELDS)
    write_csv(Path(out_dir) / "claims_to_downgrade.csv", [c for c in claims if c.get("causal_overclaim") or c.get("needs_source_data")], CLAIM_FIELDS)
    return packet


def recommend_action(needs_citation: bool, needs_source_data: bool, over_causal: bool, low_n: bool) -> str:
    actions = []
    if needs_citation:
        actions.append("add citation evidence")
    if needs_source_data:
        actions.append("link to figure/table/source_data or downgrade to qualitative wording")
    if over_causal:
        actions.append("replace causal wording with association/hypothesis wording unless mechanistic evidence is provided")
    if low_n:
        actions.append("add low-n limitation or use conservative wording")
    return "; ".join(actions) if actions else "no action"
