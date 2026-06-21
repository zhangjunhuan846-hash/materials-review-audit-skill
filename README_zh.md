# materials-review-audit-skill

**面向化工与材料综述的多 agent 审稿审计 Skill：检查正文主张、图表数据、`source_data`、Excel 数据库和引用证据是否一致。**

英文定位：

> A Codex-native multi-agent skill for chemical and materials engineering review manuscripts, focusing on claim verification, source-data consistency, figure-text alignment, descriptor database audit, and token-saving JSON-based review workflows.

## 这个项目解决什么问题

材料综述在投稿前最容易出问题的地方不是“不会写”，而是多轮修改后出现内部不一致：

- 正文说“正相关/负相关/显著提高”，但图里的方向不支持；
- 定量图没有对应 `source_data/*.csv` 或 Excel sheet；
- 正文、SI、图注、数据库里的样本数不一致；
- BET、d002、ID/IG、XPS N/O、孔容、载量、电极厚度、压实密度、ICE、容量、比电容等字段缺失、混乱或异常；
- 相关性结论被写成因果机制；
- 高风险判断没有反方审计；
- 每个 agent 都重复读取全文，浪费 token 且容易引入新不一致。

这个 skill 把上述问题转成结构化 ledger、JSON 中间文件和 P0/P1/P2 投稿前闸门。

## 7 个核心功能

1. **Claim Ledger**：拆解关键结论句，标记是否需要引用、source data、是否过度因果化、是否只是趋势性描述。
2. **Figure–Text Consistency Audit**：检查正文趋势描述是否被图表/source data 支持。
3. **Source Data Ledger**：检查每张定量图是否有对应 `source_data/*.csv` 或 Excel sheet。
4. **Descriptor Database Audit**：专门审计材料综述中的结构、电化学和电极工程字段。
5. **Conflict Gate**：P0/P1 高风险判断进入 advocate / skeptic / arbiter 流程。
6. **Token-saving Context Pack**：先生成 `draft_map.json`、`selected_context.json`、`evidence_pack.json`，避免反复把全文塞给模型。
7. **Submission Readiness Report**：输出 P0/P1/P2、ready/not ready、缺失文件清单、人工视觉 QA 清单。

## 快速运行

```bash
pip install -r requirements.txt
pip install -e .
python examples/run_demo.py
```

或：

```bash
python -m materials_review_audit.cli audit \
  --manuscript examples/input/manuscript_excerpt.md \
  --figures examples/input/figures_manifest.json \
  --source-data-dir examples/input/source_data \
  --database examples/input/databases/descriptor_database.csv \
  --reference-numbers examples/input/reference_numbers.csv \
  --out outputs/demo_audit
```

## 输出文件

- `audit_report.md`：投稿准备度报告。
- `claim_ledger.csv`：关键结论账本。
- `figure_text_mismatch.csv`：图文方向冲突。
- `source_data_ledger.csv`：图与源数据对应关系。
- `descriptor_coverage_audit.csv`：描述符覆盖率。
- `descriptor_warnings.csv`：异常值与字段风险。
- `conflict_gate_cases.csv`：高风险 advocate / skeptic / arbiter 审计。
- `missing_files.csv`：缺失文件清单。
