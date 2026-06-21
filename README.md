# Materials Review Audit Skill

**A Codex-native multi-agent skill for chemical and materials engineering review manuscripts**, focusing on claim verification, source-data consistency, figure-text alignment, descriptor database audit, and token-saving JSON-based review workflows.

中文定位：**面向化工与材料综述的多 agent 审稿审计 Skill**。它检查正文主张、图表数据、`source_data/`、Excel/CSV 数据库和引用证据是否一致，特别适合材料化学、电化学储能、AI for Materials、文献数据库驱动型综述。

## Why this project is narrow

This is not a generic literature-writing assistant. It is a submission-readiness audit workflow for review manuscripts that contain:

- curated descriptor databases;
- PRISMA-style screening counts;
- descriptor coverage heatmaps;
- Spearman/correlation heatmaps;
- missingness/source-data tables;
- claims that must be tied to figures, databases, and citations.

## Seven core functions

| Function | Implemented output | Purpose |
|---|---|---|
| Claim Ledger | `state/03_claim_ledger.json`, `claim_ledger.csv` | Splits key conclusions into claims and marks citation need, source-data need, causal overreach, and trend/association language. |
| Figure–Text Consistency Audit | `state/08_findings.json`, `figure_text_mismatch.csv` | Flags cases where text says positive/negative/increased/decreased but figure source data gives the opposite or near-zero direction. |
| Source Data Ledger | `state/04_source_data_ledger.json`, `source_data_ledger.csv`, `missing_files.csv` | Requires every quantitative figure to have matching `source_data/*.csv` or Excel sheet. |
| Descriptor Database Audit | `state/05_descriptor_audit.json`, `descriptor_coverage_audit.csv`, `descriptor_warnings.csv` | Audits materials descriptors such as BET, d002, ID/IG, N/O, pore volume, loading, thickness, density, ICE, capacity, and capacitance. |
| Conflict Gate | `state/09_conflict_gate.json`, `conflict_gate_cases.csv` | Routes P0/P1 high-risk issues into advocate / skeptic / arbiter review. |
| Token-saving Context Pack | `state/draft_map.json`, `state/selected_context.json`, `state/evidence_pack.json` | Avoids passing the whole manuscript between agents; each downstream agent reads compact JSON context. |
| Submission Readiness Report | `audit_report.md`, `audit_findings.csv` | Produces P0/P1/P2 findings, ready/not-ready judgment, missing files, and manual visual QA checklist. |

## Multi-agent JSON workflow

```text
manuscript / SI / figures / source_data / reference_numbers
        |
        v
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
10_report_writer_agent        -> audit_report.md + CSV ledgers
```

The state files are deliberately compact. Codex or another LLM reviewer can read `selected_context.json` and `evidence_pack.json` instead of the full draft, reducing token usage and improving reproducibility.

## Repository layout

```text
materials-review-audit-skill/
├── README.md
├── skill.md
├── AGENTS.md
├── config/audit_rules.yaml
├── schemas/
├── prompts/
├── src/materials_review_audit/
│   ├── cli.py
│   ├── context_pack.py
│   ├── ledger.py
│   ├── claims.py
│   ├── source_data.py
│   ├── descriptor_audit.py
│   ├── figures.py
│   ├── consistency.py
│   ├── conflict_gate.py
│   └── report.py
├── examples/
└── tests/
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Quick demo

```bash
python examples/run_demo.py
```

Or directly:

```bash
python -m materials_review_audit.cli audit \
  --manuscript examples/input/manuscript_excerpt.txt \
  --source-dir examples/input \
  --figures examples/input/figures_manifest.json \
  --reference examples/input/reference_numbers.csv \
  --out outputs/demo_audit
```

## Expected outputs

```text
outputs/demo_audit/
├── state/
│   ├── 01_inventory.json
│   ├── draft_map.json
│   ├── selected_context.json
│   ├── evidence_pack.json
│   ├── 02_number_ledger.json
│   ├── 03_claim_ledger.json
│   ├── 04_source_data_ledger.json
│   ├── 05_descriptor_audit.json
│   ├── 06_figure_manifest.json
│   ├── 08_findings.json
│   └── 09_conflict_gate.json
├── audit_report.md
├── audit_findings.csv
├── number_ledger.csv
├── claim_ledger.csv
├── claims_to_downgrade.csv
├── source_data_ledger.csv
├── missing_files.csv
├── descriptor_coverage_audit.csv
├── descriptor_warnings.csv
├── figure_text_mismatch.csv
└── conflict_gate_cases.csv
```

## Real review project structure

```text
my_review_project/
├── manuscript/review.docx
├── si/supplementary_information.docx
├── figures/fig2_prisma.png
├── figures/fig3_coverage_heatmap.png
├── figures/fig7_spearman_heatmap.png
├── source_data/fig2_prisma_counts.csv
├── source_data/fig3_coverage.csv
├── source_data/fig7_spearman.csv
├── figures_manifest.json
└── reference_numbers.csv
```

`figures_manifest.json` example:

```json
{
  "figures": [
    {
      "figure_id": "Fig.7",
      "figure_type": "spearman_heatmap",
      "source_data": "fig7_spearman.csv",
      "caption": "Descriptor-performance Spearman correlation heatmap."
    }
  ]
}
```

`reference_numbers.csv` example:

```csv
key,expected_value,unit,scope,source,notes
LIB_reports_included,95,count,main_text,database,Final PRISMA count
SIB_reports_included,93,count,main_text,database,Final PRISMA count
SC_reports_included,148,count,main_text,database,Final PRISMA count
LIB_sample_records,101,count,database,excel,Final sample-level records
SIB_sample_records,99,count,database,excel,Final sample-level records
SC_sample_records,154,count,database,excel,Final sample-level records
```

## Severity convention

| Severity | Meaning | Typical action |
|---|---|---|
| P0 | Must fix before submission | Wrong sample count, source-data missing for quantitative figure, figure-text direction mismatch, unsupported causal claim. |
| P1 | Strongly recommended fix | Missing n, ambiguous subset, missing citation/source-data pointer, descriptor database warning. |
| P2 | Optional polish / packaging issue | Orphan source-data file, low-n figure note, wording precision. |

## Materials descriptor fields recognized

The descriptor audit is intentionally adapted to chemical and materials engineering review manuscripts. It recognizes aliases for:

`BET`, `d002`, `ID/IG`, `XPS_N`, `XPS_O`, `total_pore_volume`, `micropore_volume`, `loading`, `electrode_thickness`, `compacted_density`, `ICE`, `capacity`, `capacitance`, and `current_density`.

## Current scope and limitations

The deterministic Python layer performs conservative parsing and audit triage. It does not replace human review of figure images, final captions, or source papers. For high-risk findings, the Conflict Gate deliberately keeps the issue open until a human verifies the subset definition, source-data table, and exact manuscript wording.
