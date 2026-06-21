# Materials Review Audit Skill

## Purpose

Use this skill to audit chemical and materials engineering review manuscripts for internal consistency before submission.

The skill is optimized for database-driven review articles in materials chemistry, electrochemical energy storage, carbon materials, catalysts, and AI for Materials. It checks whether manuscript claims, figure captions, figure source data, supplementary information, and descriptor databases tell the same story.

## Core positioning

A Codex-native multi-agent skill for chemical and materials engineering review manuscripts, focusing on:

1. claim verification;
2. source-data consistency;
3. figure-text alignment;
4. descriptor database audit;
5. conflict-gated high-risk review;
6. token-saving JSON context packs;
7. submission-readiness reporting.

中文定位：面向化工与材料综述的多 agent 审稿审计 Skill：检查正文主张、图表数据、`source_data`、Excel 数据库和引用证据是否一致。

## When to use

Use this skill when the user asks to:

- check whether a review manuscript matches updated Excel/CSV databases;
- verify that figure captions, figure source data, and manuscript claims are consistent;
- audit sample counts, PRISMA counts, descriptor coverage, or correlation heatmaps;
- detect over-strong claims unsupported by the database;
- audit BET, d002, ID/IG, N/O, pore volume, loading, electrode thickness, compacted density, ICE, capacity, and capacitance fields;
- produce a submission-readiness audit with P0/P1/P2 findings;
- create a number ledger, claim ledger, source-data ledger, or descriptor audit report.

## Required operating principle

Do not pass the full manuscript between agents. First create compact JSON context files:

```text
state/draft_map.json
state/selected_context.json
state/evidence_pack.json
```

Each later agent should read only the JSON packets it needs.

## Agent workflow

### 01 Inventory Agent

Creates `state/01_inventory.json`.

Responsibilities:
- identify manuscript, SI, source-data, figure manifest, and reference-number ledger files;
- compute file hashes;
- list missing expected files where possible.

### Context Pack Agent

Creates:

```text
state/draft_map.json
state/selected_context.json
state/evidence_pack.json
```

Responsibilities:
- map manuscript lines and headings;
- extract only lines that contain claims, numbers, figure mentions, or material descriptors;
- prepare compact evidence chunks for later agents.

### 02 Number Ledger Agent

Creates `state/02_number_ledger.json` and `number_ledger.csv`.

Responsibilities:
- extract sample counts, PRISMA counts, n values, percentages, performance values, correlation coefficients;
- compare against `reference_numbers.csv`;
- flag number drift as P0 when reference-ledger conflict is detected.

### 03 Claim Ledger Agent

Creates `state/03_claim_ledger.json` and `claim_ledger.csv`.

For each important claim, mark:
- claim category: `database_derived`, `statistical_association`, `mechanistic_hypothesis`, or `conceptual_framing`;
- whether citation is needed;
- whether source-data support is needed;
- whether the claim is over-causalized;
- whether wording should be downgraded.

### 04 Source Data Ledger Agent

Creates `state/04_source_data_ledger.json`, `source_data_ledger.csv`, and `missing_files.csv`.

Rules:
- every quantitative figure must have a matching CSV/XLSX source-data file;
- missing source data for quantitative heatmaps, PRISMA diagrams, coverage heatmaps, and missingness heatmaps is P0;
- orphan source-data files are P2 packaging issues.

### 05 Descriptor Database Audit Agent

Creates `state/05_descriptor_audit.json`, `descriptor_coverage_audit.csv`, and `descriptor_warnings.csv`.

Recognized material fields:
- BET / specific surface area;
- d002 / interlayer spacing;
- Raman ID/IG;
- XPS N and O;
- total pore volume and micropore volume;
- mass loading;
- electrode thickness;
- compacted/tap density;
- ICE;
- capacity;
- capacitance;
- current density.

Checks:
- field coverage;
- column aliases;
- missing core descriptors;
- physically implausible values;
- likely OCR/unit errors.

### 06 Figure–Text Agent

Creates `state/06_figure_manifest.json`.

Responsibilities:
- bind each figure to source-data;
- infer key values from source-data;
- read correlation values and n values;
- prepare evidence for figure-text consistency checking.

### 08 Consistency Agent

Creates `state/08_findings.json`.

Responsibilities:
- combine number ledger, claim ledger, source-data ledger, descriptor audit, and figure manifest;
- flag P0/P1/P2 issues;
- specifically check whether textual direction agrees with source-data direction where possible.

### 09 Conflict Gate Agent

Creates `state/09_conflict_gate.json`.

For P0/P1 high-risk findings, create:
- advocate position;
- skeptic counter-checks;
- arbiter decision and next action.

### 10 Report Writer Agent

Creates:

```text
audit_report.md
audit_findings.csv
claim_ledger.csv
source_data_ledger.csv
descriptor_coverage_audit.csv
conflict_gate_cases.csv
```

Final report must include:
- P0: must fix;
- P1: strongly recommended fix;
- P2: optional optimization;
- ready / not ready judgment;
- missing files checklist;
- manual visual QA checklist.

## P0 examples

- Main text reports LIB records as 97, but final reference ledger says 101.
- Figure 7 source data has Spearman rho = -0.02 for d002 vs SIB-ICE, but the caption claims a positive association.
- A quantitative heatmap has no source-data file.
- A database-derived trend is written as “proves” or “determines”.

## P1 examples

- A correlation heatmap reports rho but omits n.
- A claim clearly needs a citation, but none is detected in the local sentence.
- A claim should point to source data but no figure/source pointer is present.
- The descriptor database lacks expected aliases for key fields.

## P2 examples

- A source-data file exists but is not connected to any figure manifest entry.
- Low-n correlation cells need an exploratory/grey-out note.
- Wording should distinguish descriptor coverage from correlation strength.
