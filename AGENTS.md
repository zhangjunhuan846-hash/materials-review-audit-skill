# Agent Protocol

This repository uses a JSON-first multi-agent protocol. Agents must not pass the full manuscript to each other. Each agent writes a compact JSON state file and downstream agents consume only the state files they need.

## Mandatory state order

```text
01_inventory_agent            -> state/01_inventory.json
context_pack_agent            -> state/draft_map.json
                              -> state/selected_context.json
                              -> state/evidence_pack.json
02_number_ledger_agent        -> state/02_number_ledger.json
03_claim_ledger_agent         -> state/03_claim_ledger.json
04_source_data_ledger_agent   -> state/04_source_data_ledger.json
05_descriptor_database_agent  -> state/05_descriptor_audit.json
06_figure_text_agent          -> state/06_figure_manifest.json
08_consistency_agent          -> state/08_findings.json
09_conflict_gate_agent        -> state/09_conflict_gate.json
10_report_writer_agent        -> audit_report.md
```

## Agent boundaries

- Inventory Agent handles files and hashes only.
- Context Pack Agent handles token-saving manuscript maps only.
- Number Ledger Agent handles numeric drift and reference number conflicts.
- Claim Ledger Agent handles wording, evidence need, and causal overreach.
- Source Data Ledger Agent handles figure-to-source-data availability.
- Descriptor Database Agent handles materials descriptor columns and value plausibility.
- Figure–Text Agent extracts quantitative source-data summaries and key figure values.
- Consistency Agent merges state and creates P0/P1/P2 findings.
- Conflict Gate Agent reviews high-risk findings with advocate / skeptic / arbiter structure.
- Report Writer Agent summarizes findings and readiness only; it must not invent new evidence.

## Conflict Gate rules

A finding must enter the Conflict Gate when any of the following occurs:

- severity is P0;
- severity is P1 and category is claim strength, figure-text mismatch, source-data ledger, or descriptor range;
- the finding would change a manuscript conclusion;
- the finding would require checking original source papers.

Each Conflict Gate case must contain:

```json
{
  "case_id": "gate_0001",
  "finding_id": "P0-001",
  "advocate": {},
  "skeptic": {},
  "arbiter": {}
}
```

## Materials descriptor audit rules

The Descriptor Database Agent must look for chemical/materials fields using aliases, not exact column names only. Core descriptors include BET, d002, ID/IG, XPS N/O, pore volume, mass loading, electrode thickness, compacted density, ICE, capacity, capacitance, and current density.

Values outside soft physical ranges are not automatically corrected. They must be flagged for manual verification.

## Severity policy

- P0: must fix before submission.
- P1: strongly recommended fix before submission.
- P2: optional polish or packaging issue.

Never downgrade a P0 just because the correction is inconvenient. If the automated parser may be wrong, keep the issue open with `status: needs_manual_check`.
