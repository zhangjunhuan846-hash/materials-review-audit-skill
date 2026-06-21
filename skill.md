# materials-review-audit-skill

## Purpose

Use this skill when auditing chemical and materials engineering review manuscripts before submission. The skill checks whether manuscript claims, figures, source-data files, descriptor databases, and citation evidence are mutually consistent.

This is not a writing skill. Do not rewrite the manuscript unless the user explicitly asks. The primary output is a structured audit package.

## Core tasks

1. Build a token-saving context pack:
   - `draft_map.json`
   - `selected_context.json`
   - `evidence_pack.json`

2. Build a Claim Ledger:
   - split key conclusion sentences into claims;
   - mark claims that need citation;
   - mark claims that need source data;
   - mark causal overclaim;
   - mark trend-only claims;
   - assign P0/P1/P2 where applicable.

3. Build a Source Data Ledger:
   - map every quantitative figure to `source_data/*.csv` or Excel sheet;
   - flag missing source data;
   - flag orphan source data;
   - flag figures that require manual visual QA.

4. Run Descriptor Database Audit:
   - detect field coverage and missingness;
   - audit materials descriptors including BET, d002, ID/IG, XPS N/O, total pore volume, micropore volume, mass loading, electrode thickness, compacted density, ICE, capacity, capacitance, current density, voltage window;
   - flag physically implausible or suspicious values;
   - distinguish scientific descriptors from engineering descriptors.

5. Run Figure–Text Consistency Audit:
   - detect text directions such as positive correlation, negative correlation, increased, decreased, improved, reduced;
   - compare against source-data direction when available;
   - flag contradictions and unsupported strong claims.

6. Run Conflict Gate:
   - send high-risk P0/P1 findings through advocate / skeptic / arbiter review;
   - do not silently resolve high-risk conflicts without reporting the uncertainty.

7. Generate Submission Readiness Report:
   - P0: must fix;
   - P1: strongly recommended revision;
   - P2: optional polish;
   - ready / conditionally ready / not ready;
   - missing files;
   - manual visual QA checklist.

## JSON-first rule

Use JSON packets for all agent handoffs. Do not pass the full manuscript to every agent. Each agent should load only the needed packets from `state/`.

Preferred state files:

```text
state/01_inventory.json
state/draft_map.json
state/selected_context.json
state/evidence_pack.json
state/03_claim_ledger.json
state/04_source_data_ledger.json
state/05_descriptor_audit.json
state/06_figure_text_audit.json
state/07_conflict_gate.json
```

## Severity definitions

- P0: must fix before submission.
- P1: strongly recommended revision.
- P2: optional optimization or transparency note.

Any P0 makes the manuscript package `NOT READY`. Any P1 without P0 makes it `CONDITIONALLY READY`.

## Output discipline

Always produce:

```text
audit_report.md
claim_ledger.csv
source_data_ledger.csv
descriptor_coverage_audit.csv
descriptor_warnings.csv
figure_text_mismatch.csv
conflict_gate_cases.csv
missing_files.csv
audit_findings.csv
```

If evidence is insufficient, say so. Do not invent source data, citations, or database values.
