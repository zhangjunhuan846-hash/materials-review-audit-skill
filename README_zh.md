# materials-review-audit-skill

<p align="center">
  <b>面向化工与材料综述的多 Agent 审稿审计 Skill</b><br>
  <span>Claim Verification · Source-data Consistency · Figure-text Alignment · Descriptor Database Audit · JSON-first Workflow</span>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue">
  <img alt="Workflow" src="https://img.shields.io/badge/Workflow-Multi--Agent-black">
  <img alt="Handoff" src="https://img.shields.io/badge/Handoff-JSON--first-green">
  <img alt="Domain" src="https://img.shields.io/badge/Domain-Chemical%20%26%20Materials%20Engineering-purple">
  <img alt="Status" src="https://img.shields.io/badge/Status-Submission%20QA-orange">
</p>

---

## 项目定位

`materials-review-audit-skill` 是一个 **Codex-native、JSON-first、多 Agent 协同的材料综述投稿前审计工作流**。它不负责“帮你把综述写得更像综述”，而是检查一篇化工与材料工程综述在投稿前是否存在以下硬伤：

- 正文主张是否有足够引用、图表、`source_data` 或数据库证据支撑；
- 图注和正文中的“正相关 / 负相关 / 显著提高 / 明显降低”是否真的被图中数值方向支持；
- 每张定量图是否有可追溯的 `source_data/*.csv` 或 Excel sheet；
- Excel 描述符数据库中的 BET、d002、ID/IG、XPS N/O、孔容、载量、ICE、容量、比电容等字段是否缺失、异常或口径不一致；
- 正文、SI、图表、数据库、source data 中的样本数、子集定义和统计结论是否互相冲突；
- 高风险判断是否经过 advocate / skeptic / arbiter 三方复核；
- 最终稿件是否达到 `READY / CONDITIONALLY READY / NOT READY` 的提交准备度。

> **一句话定位**：面向化工与材料综述的多 agent 审稿审计 Skill，用于检查正文主张、图表数据、`source_data`、Excel 数据库和引用证据是否一致。

英文定位：

> A Codex-native multi-agent skill for chemical and materials engineering review manuscripts, focusing on claim verification, source-data consistency, figure-text alignment, descriptor database audit, and token-saving JSON-based review workflows.

---

## 为什么需要这个 Skill

材料综述在后期最容易出现的问题，往往不是选题不重要，而是 **证据链断裂**。典型情况包括：

| 常见风险 | 审稿人可能看到的问题 | 本 Skill 的处理方式 |
|---|---|---|
| 正文结论过强 | 相关性被写成因果机制；趋势性观察被写成普适规律 | 生成 `Claim Ledger`，标记 causal overclaim、trend-only claim、missing citation |
| 图文方向冲突 | 正文说正相关，但热图或散点数据实际为负相关 / 不显著 | 生成 `figure_text_mismatch.csv`，进入 P0/P1 风险 |
| source data 缺失 | 定量图没有源数据，无法复核 | 生成 `Source Data Ledger`，缺失主图 source data 通常标为 P0/P1 |
| 数据库字段混乱 | BET、d002、ID/IG、ICE、容量等字段单位或范围异常 | 运行材料描述符规则库，输出 `descriptor_warnings.csv` |
| 样本数不一致 | 正文、SI、图注、Excel 统计数字互相不一致 | 生成 `number_ledger.csv` 和 P0 数字冲突 |
| 单模型误判 | 高风险结论只经过一次模型判断 | 进入 `Conflict Gate`：advocate / skeptic / arbiter |
| token 浪费 | 每个 agent 都读全文，成本高且容易引入新矛盾 | 先生成 `draft_map.json`、`selected_context.json`、`evidence_pack.json` |

---

## 核心能力

### 1. Claim Ledger：关键主张账本

将综述中的关键判断拆解为可审计的 claim，并标记：

- 是否需要引用；
- 是否需要 `source_data`；
- 是否存在过度因果化；
- 是否只是趋势性观察；
- 是否存在低样本量或子集口径风险；
- 建议降级表达方式。

输出：

```text
claim_ledger.csv
claims_to_downgrade.csv
state/03_claim_ledger.json
```

---

### 2. Figure–Text Consistency Audit：图文一致性审计

检查正文和图注中的趋势性描述是否被图中方向支持，例如：

- “positively correlated / 正相关”；
- “negative correlation / 负相关”；
- “significantly increased / 显著提高”；
- “substantially reduced / 明显降低”；
- “higher BET leads to improved performance / 高 BET 导致性能提升”。

如果正文说“正相关”，但 `source_data` 中 Spearman ρ 为负或接近 0，会输出图文冲突项。

输出：

```text
figure_text_mismatch.csv
state/06_figure_text_audit.json
```

---

### 3. Source Data Ledger：图表源数据账本

每张定量图都必须能追溯到源数据。该模块检查：

- 主图是否有对应 `source_data/*.csv` 或 Excel sheet；
- 图表 manifest 中声明的源数据是否真实存在；
- 是否存在 orphan source data，即文件存在但没有图引用；
- 哪些图需要人工视觉 QA。

输出：

```text
source_data_ledger.csv
missing_files.csv
state/04_source_data_ledger.json
```

---

### 4. Descriptor Database Audit：材料描述符数据库审计

面向化工与材料综述定制，而不是普通 Excel 检查。默认覆盖以下字段：

| 类别 | 字段示例 | 常见风险 |
|---|---|---|
| 结构描述符 | BET、d002、ID/IG、总孔容、微孔体积、孔径 | 单位混乱、数值极端、字段缺失 |
| 化学描述符 | XPS N、XPS O、掺杂类型、灰分、表面官能团 | wt% / at% 混用，XPS 与元素分析混用 |
| 电化学指标 | ICE、容量、倍率容量、平台容量、比电容、保持率 | ICE > 100%、倍率单位缺失、容量口径不清 |
| 电极工程参数 | 面载量、电极厚度、压实密度、粘结剂比例、导电剂比例 | 器件级外推证据不足 |
| 测试条件 | 电解液、电压窗口、电流密度、扫速、循环圈数 | 不同体系混合比较，条件不可比 |

输出：

```text
descriptor_coverage_audit.csv
descriptor_warnings.csv
state/05_descriptor_audit.json
```

---

### 5. Conflict Gate：高风险判断闸门

所有 P0/P1 高风险发现都会进入三方审计：

```text
Advocate：为什么这个问题确实严重？
Skeptic：是否可能是误判、语境不足或可接受差异？
Arbiter：最终严重等级、处理建议、是否需要人工核查。
```

这能减少单次模型判断造成的误报，也能在报告中保留不确定性。

输出：

```text
conflict_gate_cases.csv
state/07_conflict_gate.json
```

---

### 6. Token-saving Context Pack：节省 token 的上下文包

该 Skill 不要求每个 agent 反复读取整篇 manuscript。流程先生成轻量级上下文包：

```text
state/draft_map.json
state/selected_context.json
state/evidence_pack.json
```

每个 agent 只读取自己需要的局部材料，从而降低 token 消耗、减少上下文污染，并提高审计结果的一致性。

---

### 7. Submission Readiness Report：投稿准备度报告

最终报告不只是列问题，而是给出可执行的提交判断：

```text
P0：必须修复，否则不建议投稿
P1：强烈建议修复，否则可能被审稿人质疑
P2：可选优化，主要用于透明度和表达精度
```

准备度判定：

| 判定 | 条件 | 含义 |
|---|---|---|
| `NOT READY` | 存在任意 P0 | 当前版本不建议投稿 |
| `CONDITIONALLY READY` | 无 P0，但存在 P1 | 可以推进，但建议先修 P1 |
| `READY` | 无 P0/P1 | 只剩轻微透明度或格式优化 |

输出：

```text
audit_report.md
audit_findings.csv
missing_files.csv
manual_visual_qa checklist
```

---

## 工作流架构

```text
manuscript.md / manuscript.docx
figures_manifest.json
source_data/*.csv
descriptor_database.xlsx / .csv
reference_numbers.csv
citation_evidence.json optional
        │
        ▼
┌──────────────────────────────┐
│ 01 Inventory Agent            │
│ 建立文件、图表、数据库清单      │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 02 Context Pack Agent         │
│ draft_map / selected_context  │
│ evidence_pack                 │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 03 Claim Ledger Agent         │
│ 主张拆解与证据需求标记          │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 04 Source Data Ledger Agent   │
│ 图表与源数据对应关系            │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 05 Descriptor DB Audit Agent  │
│ 材料描述符覆盖率与异常值审计     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 06 Figure-Text Agent          │
│ 正文趋势描述与图中数值方向核对   │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 07 Conflict Gate Agent        │
│ advocate / skeptic / arbiter  │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│ 08 Report Writer Agent        │
│ P0/P1/P2 + readiness report   │
└──────────────────────────────┘
```

---

## 安装与快速运行

### 1. 安装

```bash
pip install -r requirements.txt
pip install -e .
```

### 2. 运行 demo

```bash
python examples/run_demo.py
```

### 3. 使用 CLI 审计自己的项目

```bash
python -m materials_review_audit.cli audit \
  --manuscript examples/input/manuscript_excerpt.md \
  --figures examples/input/figures_manifest.json \
  --source-data-dir examples/input/source_data \
  --database examples/input/databases/descriptor_database.csv \
  --reference-numbers examples/input/reference_numbers.csv \
  --out outputs/demo_audit
```

---

## 推荐输入结构

```text
project/
├── manuscript/
│   └── review_manuscript.docx
├── figures/
│   └── figures_manifest.json
├── source_data/
│   ├── fig3_descriptor_coverage.csv
│   ├── fig7_spearman_heatmap.csv
│   └── fig9_missingness.csv
├── databases/
│   └── descriptor_database.xlsx
├── si/
│   └── reference_numbers.csv
└── citations/
    └── citation_evidence.json optional
```

`figures_manifest.json` 示例：

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

`reference_numbers.csv` 示例：

```csv
label,expected_value,tolerance,unit,notes
LIB_records,101,0,count,Final sample-level records for LIB
SIB_records,99,0,count,Final sample-level records for SIB
SC_records,154,0,count,Final sample-level records for aqueous SC
```

---

## 输出文件说明

```text
outputs/demo_audit/
├── audit_report.md                  # 投稿准备度报告
├── audit_findings.csv               # 全部 P0/P1/P2 发现
├── claim_ledger.csv                 # 主张账本
├── claims_to_downgrade.csv          # 建议降级表达的 claim
├── source_data_ledger.csv           # 图表-source data 对应关系
├── missing_files.csv                # 缺失文件清单
├── descriptor_coverage_audit.csv    # 描述符覆盖率审计
├── descriptor_warnings.csv          # 描述符异常值与字段风险
├── figure_text_mismatch.csv         # 图文趋势冲突
├── conflict_gate_cases.csv          # advocate / skeptic / arbiter 高风险复核
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

---

## 在 Codex / OpenClaw 中使用

可以直接给 Codex / OpenClaw 下达如下指令：

```text
Use the materials-review-audit-skill.
Audit my chemical and materials engineering review manuscript package.

Inputs:
- manuscript/review.docx
- figures/figures_manifest.json
- source_data/*.csv
- databases/descriptor_database.xlsx
- si/reference_numbers.csv

Requirements:
1. Run the JSON-first token-saving workflow first.
2. Build draft_map.json, selected_context.json, and evidence_pack.json.
3. Generate Claim Ledger, Source Data Ledger, Descriptor Database Audit,
   Figure–Text Consistency Audit, Conflict Gate cases, and Submission Readiness Report.
4. Do not rewrite the manuscript unless explicitly requested.
5. Do not invent citations, source data, sample counts, or database values.
6. Report P0/P1/P2 findings with file-level evidence.
```

---

## 与上游/下游项目的关系

该 Skill 适合作为材料综述投稿前 QA 中枢，与其他工具形成完整工作流：

```text
ai-extracted-data-cleaner
  清洗 AI / OCR / PDF parser 提取的数据
        ↓
materials-review-audit-skill
  审计 manuscript + figures + source_data + descriptor database
        ↓
offline-bo-materials-skill
  用清洗后的数据库做离线贝叶斯优化和候选材料筛选
        ↓
hard-carbon-atomistic-model-builder
  构建 DFT / ASE / VASP / QE 机制验证模型
```

---

## 适用场景

- 生物质碳、硬碳、多孔碳、储能材料综述；
- LIB / SIB / KIB / 水系超级电容器等跨体系材料数据库综述；
- 含大量统计图、热图、PRISMA 流程、描述符覆盖率图的 review manuscript；
- 需要提交前核对正文、SI、source data、Excel 数据库、图表的一致性；
- 需要让 Codex 以低 token 成本执行多轮审计的研究型项目。

---

## 当前边界与限制

- 该 Skill 是审计工具，不替代人工审稿判断；
- 图像本身的视觉错误仍需要人工 QA，尤其是颜色条、坐标轴、显著性标记和图中文字；
- 如果 manuscript 中没有提供足够上下文，claim-level 判断会标记为 evidence insufficient；
- 如果 source data 命名混乱，建议先整理 `figures_manifest.json`；
- 不会伪造引用、DOI、source data、数据库值或统计结果。

---

## 推荐 GitHub 展示方式

建议在仓库中加入一个脱敏 case study：

```text
case_studies/biomass_carbon_review_demo/
├── manuscript_excerpt.md
├── figures_manifest.json
├── source_data/
│   ├── fig3_descriptor_coverage.csv
│   ├── fig7_spearman_heatmap.csv
│   └── fig9_missingness.csv
├── descriptor_database.csv
├── reference_numbers.csv
└── audit_outputs/
    ├── audit_report.md
    ├── claim_ledger.csv
    ├── source_data_ledger.csv
    └── figure_text_mismatch.csv
```

这样可以清楚展示：这个项目不是普通 prompt 包，而是一个面向材料综述提交前质量控制的可复现审计工作流。

---

## Roadmap

- [ ] 增加 `.docx` 段落级定位和批注导出；
- [ ] 支持 Excel 多 sheet source data 自动索引；
- [ ] 增加 citation evidence ledger；
- [ ] 增加 figure caption 与 source data 的数值方向比对；
- [ ] 增加 PRISMA / descriptor heatmap 专用审计模板；
- [ ] 增加 HTML submission-readiness dashboard；
- [ ] 增加真实材料综述脱敏 case study。

---

## License

MIT License.
