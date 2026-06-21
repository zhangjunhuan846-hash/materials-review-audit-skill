# Multi-agent protocol

This repository implements a JSON-first multi-agent audit protocol. Each agent receives a narrow packet and writes a deterministic output packet. This reduces token usage and prevents each agent from reinterpreting the whole manuscript.

## Agent order

| Step | Agent | Reads | Writes |
|---|---|---|---|
| 01 | Inventory Agent | manuscript, figure manifest, source-data directory, database path | `state/01_inventory.json` |
| 02 | Context Pack Agent | `01_inventory.json`, manuscript | `draft_map.json`, `selected_context.json`, `evidence_pack.json` |
| 03 | Claim Ledger Agent | `selected_context.json`, `evidence_pack.json` | `03_claim_ledger.json` |
| 04 | Source Data Ledger Agent | `evidence_pack.json`, `figures_manifest.json`, source-data directory | `04_source_data_ledger.json` |
| 05 | Descriptor Database Audit Agent | descriptor database, `evidence_pack.json` | `05_descriptor_audit.json` |
| 06 | Figure–Text Consistency Agent | `03_claim_ledger.json`, source-data files, `04_source_data_ledger.json` | `06_figure_text_audit.json` |
| 07 | Conflict Gate Agent | all P0/P1 findings | `07_conflict_gate.json` |
| 08 | Report Writer Agent | all ledgers | `audit_report.md`, CSV outputs |

## Conflict Gate rule

Any finding that meets one of the following conditions must enter Conflict Gate:

- P0 severity;
- P1 severity with direct effect on a main conclusion;
- figure-text direction contradiction;
- source data missing for a quantitative main figure;
- descriptor value physically impossible or suspicious enough to change interpretation;
- number conflict across manuscript, SI, figures, and database.

Conflict Gate output must include:

```json
{
  "case_id": "CG-001",
  "finding_id": "F-001",
  "advocate": "Why the finding is valid and should be fixed.",
  "skeptic": "Alternative explanation or reason the finding may be overcalled.",
  "arbiter": "Final decision and recommended action.",
  "final_severity": "P0"
}
```

## Style rules

- Never fabricate citations, source data, or numerical evidence.
- Separate database-derived claims, statistical associations, mechanistic hypotheses, and conceptual framing.
- Prefer conservative wording when n is small, fields are missing, or source data are incomplete.
- Keep the final report actionable: file, location, problem, evidence, severity, recommended fix.
