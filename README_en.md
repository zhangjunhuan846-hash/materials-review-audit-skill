# materials-review-audit-skill

**A Codex-native multi-agent skill for chemical and materials engineering review manuscripts, focusing on claim verification, source-data consistency, figure-text alignment, descriptor database audit, and token-saving JSON-based review workflows.**

**中文定位：**面向化工与材料综述的多 agent 审稿审计 Skill：检查正文主张、图表数据、`source_data`、Excel 数据库和引用证据是否一致。

This repository is not a generic paper-writing prompt pack. It is a submission-readiness audit workflow for materials review manuscripts. It is designed for review articles where the manuscript, figures, `source_data/*.csv`, descriptor databases, and citation evidence must remain internally consistent.

## Why this skill exists

Chemical and materials engineering reviews often fail at the final quality-control stage, not because the topic is weak, but because the manuscript package becomes internally inconsistent after repeated revisions:

- the text claims a positive or negative trend that the figure does not support;
- a figure has no matching `source_data/*.csv` or Excel sheet;
- the manuscript, SI, figure caption, and database report different sample counts;
- key descriptors such as BET, d002, ID/IG, XPS N/O, pore volume, mass loading, electrode thickness, compacted density, ICE, capacity, and capacitance are mixed, missing, or out of range;
- association claims are written as causal mechanisms;
- high-risk judgments are made by a single model pass without an advocate/skeptic/arbiter review;
- the full manuscript is repeatedly sent to every agent, wasting context and increasing inconsistency.

This skill turns those problems into explicit ledgers, JSON packets, and P0/P1/P2 submission gates.

## Core capabilities

| Capability | What it audits | Main output |
|---|---|---|
| **1. Claim Ledger** | Extracts key conclusion sentences and flags missing citation, missing source data, causal overclaim, low-n wording, and trend-only claims. | `claim_ledger.csv`, `state/03_claim_ledger.json` |
| **2. Figure–Text Consistency Audit** | Checks whether text statements such as “positive correlation”, “negative correlation”, “significantly increased”, or “decreased” are supported by figure/source-data directions. | `figure_text_mismatch.csv`, `state/06_figure_text_audit.json` |
| **3. Source Data Ledger** | Requires quantitative figures to have corresponding `source_data/*.csv` or Excel sheets; flags missing and orphan source-data files. | `source_data_ledger.csv`, `missing_files.csv`, `state/04_source_data_ledger.json` |
| **4. Descriptor Database Audit** | Materials-specific audit of BET, d002, ID/IG, XPS N/O, pore volume, mass loading, electrode thickness, compacted density, ICE, capacity, capacitance, current density, and voltage window. | `descriptor_coverage_audit.csv`, `descriptor_warnings.csv`, `state/05_descriptor_audit.json` |
| **5. Conflict Gate** | Sends high-risk findings through advocate / skeptic / arbiter review before final severity assignment. | `conflict_gate_cases.csv`, `state/07_conflict_gate.json` |
| **6. Token-saving Context Pack** | Generates `draft_map.json`, `selected_context.json`, and `evidence_pack.json` so each agent reads only the local material it needs. | `state/draft_map.json`, `state/selected_context.json`, `state/evidence_pack.json` |
| **7. Submission Readiness Report** | Produces P0/P1/P2 findings, ready/not-ready decision, missing-file list, and manual visual-QA checklist. | `audit_report.md`, `audit_findings.csv` |

## Workflow

```text
Manuscript + figures_manifest.json + source_data/ + descriptor_database.xlsx/csv
        │
        ▼
01 Inventory Agent
        ├── state/01_inventory.json
        │
        ▼
02 Context Pack Agent
        ├── state/draft_map.json
        ├── state/selected_context.json
        └── state/evidence_pack.json
        │
        ▼
03 Claim Ledger Agent
        ├── state/03_claim_ledger.json
        └── claim_ledger.csv
        │
        ▼
04 Source Data Ledger Agent
        ├── state/04_source_data_ledger.json
        ├── source_data_ledger.csv
        └── missing_files.csv
        │
        ▼
05 Descriptor Database Audit Agent
        ├── state/05_descriptor_audit.json
        ├── descriptor_coverage_audit.csv
        └── descriptor_warnings.csv
        │
        ▼
06 Figure–Text Consistency Agent
        ├── state/06_figure_text_audit.json
        └── figure_text_mismatch.csv
        │
        ▼
07 Conflict Gate Agent
        ├── state/07_conflict_gate.json
        └── conflict_gate_cases.csv
        │
        ▼
08 Report Writer Agent
        ├── audit_report.md
        └── audit_findings.csv
```

## Severity system

| Level | Meaning | Typical examples |
|---|---|---|
| **P0** | Must fix before submission. | Missing source data for a quantitative figure; sample count conflicts; physically impossible descriptor values; figure-text contradiction for a main conclusion. |
| **P1** | Strongly recommended revision. | Claim needs citation; claim needs source data; over-causal wording; high missingness in engineering descriptors. |
| **P2** | Optional optimization or transparency note. | Low-n caution; orphan source-data file; wording precision; manual visual-QA reminder. |

Readiness decision:

- `NOT READY`: at least one P0 finding.
- `CONDITIONALLY READY`: no P0 but at least one P1 finding.
- `READY`: no P0/P1 findings; only P2 or no findings.

## Inputs

Minimum input package:

```text
project/
├── manuscript.md                 # or .txt; .docx supported when python-docx is installed
├── figures_manifest.json          # required for source-data checks
├── source_data/
│   ├── fig3_descriptor_coverage.csv
│   ├── fig7_spearman_heatmap.csv
│   └── fig9_missingness.csv
├── descriptor_database.xlsx       # or .csv
└── reference_numbers.csv          # optional but recommended
```

### `figures_manifest.json`

```json
[
  {
    "figure_id": "Fig.7",
    "title": "Descriptor-performance Spearman correlation heatmap",
    "figure_type": "correlation_heatmap",
    "quantitative": true,
    "source_data_required": true,
    "expected_source_files": ["fig7_spearman_heatmap.csv"],
    "manual_visual_qa": true
  }
]
```

### `reference_numbers.csv`

```csv
label,expected_value,tolerance,unit,notes
LIB_records,101,0,count,Final sample-level records for LIB
SIB_records,99,0,count,Final sample-level records for SIB
SC_records,154,0,count,Final sample-level records for aqueous SC
```

## Quick start

```bash
pip install -r requirements.txt
pip install -e .
python examples/run_demo.py
```

Or run the CLI directly:

```bash
python -m materials_review_audit.cli audit \
  --manuscript examples/input/manuscript_excerpt.md \
  --figures examples/input/figures_manifest.json \
  --source-data-dir examples/input/source_data \
  --database examples/input/databases/descriptor_database.csv \
  --reference-numbers examples/input/reference_numbers.csv \
  --out outputs/demo_audit
```

## Outputs

```text
outputs/demo_audit/
├── audit_report.md
├── audit_findings.csv
├── claim_ledger.csv
├── claims_to_downgrade.csv
├── source_data_ledger.csv
├── missing_files.csv
├── descriptor_coverage_audit.csv
├── descriptor_warnings.csv
├── figure_text_mismatch.csv
├── conflict_gate_cases.csv
└── state/
    ├── 01_inventory.json
    ├── draft_map.json
    ├── selected_context.json
    ├── evidence_pack.json
    ├── 03_claim_ledger.json
    ├── 04_source_data_ledger.json
    ├── 05_descriptor_audit.json
    ├── 06_figure_text_audit.json
    └── 07_conflict_gate.json
```

## Repository structure

```text
materials-review-audit-skill/
├── README.md
├── README_zh.md
├── skill.md
├── AGENTS.md
├── config/audit_rules.yaml
├── prompts/                         # agent-level instructions
├── schemas/                         # JSON packet schemas
├── src/materials_review_audit/       # baseline deterministic audit engine
├── examples/                         # demo manuscript, source data, database
├── tests/                            # regression tests
└── docs/architecture.md
```

## Codex / OpenClaw usage

Example instruction:

```text
Use the materials-review-audit-skill.
Audit my materials review manuscript package.
Inputs:
- manuscript/review.docx
- figures/figures_manifest.json
- source_data/*.csv
- databases/descriptors.xlsx
- SI/reference_numbers.csv

Run the token-saving workflow first.
Then produce the Claim Ledger, Source Data Ledger, Descriptor Database Audit,
Figure–Text Consistency Audit, Conflict Gate cases, and Submission Readiness Report.
Do not rewrite the manuscript unless I explicitly ask. Return P0/P1/P2 findings with file-level evidence.
```

## What this skill does not do

- It does not claim to replace expert review.
- It does not automatically fabricate citations or source data.
- It does not decide scientific truth from a single correlation.
- It does not guarantee permission compliance for adapted figures; those remain manual visual and copyright QA tasks.

## Recommended case-study naming

For a GitHub demo without exposing unpublished data:

```text
case_studies/biomass_carbon_review_demo/
├── manuscript_excerpt.md
├── figures_manifest.json
├── source_data/
├── descriptor_database_redacted.csv
└── audit_outputs/
```

This makes the project understandable to materials researchers: it is a reproducible submission-QA workflow, not a generic AI writing assistant.
