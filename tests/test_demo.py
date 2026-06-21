from pathlib import Path

from materials_review_audit.cli import main
from materials_review_audit.utils import read_json


def test_demo_runs(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "audit"
    main([
        "audit",
        "--manuscript", str(root / "examples/input/manuscript_excerpt.md"),
        "--figures", str(root / "examples/input/figures_manifest.json"),
        "--source-data-dir", str(root / "examples/input/source_data"),
        "--database", str(root / "examples/input/databases/descriptor_database.csv"),
        "--reference-numbers", str(root / "examples/input/reference_numbers.csv"),
        "--out", str(out),
    ])
    assert (out / "audit_report.md").exists()
    assert (out / "claim_ledger.csv").exists()
    assert (out / "source_data_ledger.csv").exists()
    assert (out / "descriptor_warnings.csv").exists()
    assert (out / "figure_text_mismatch.csv").exists()
    assert (out / "state/draft_map.json").exists()


def test_missing_fig9_flagged(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "audit"
    main([
        "audit",
        "--manuscript", str(root / "examples/input/manuscript_excerpt.md"),
        "--figures", str(root / "examples/input/figures_manifest.json"),
        "--source-data-dir", str(root / "examples/input/source_data"),
        "--database", str(root / "examples/input/databases/descriptor_database.csv"),
        "--reference-numbers", str(root / "examples/input/reference_numbers.csv"),
        "--out", str(out),
    ])
    ledger = read_json(out / "state/04_source_data_ledger.json")
    assert any("fig9_missingness.csv" in str(x) for x in ledger["missing_files"])


def test_conflict_gate_has_high_risk_cases(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "audit"
    main([
        "audit",
        "--manuscript", str(root / "examples/input/manuscript_excerpt.md"),
        "--figures", str(root / "examples/input/figures_manifest.json"),
        "--source-data-dir", str(root / "examples/input/source_data"),
        "--database", str(root / "examples/input/databases/descriptor_database.csv"),
        "--reference-numbers", str(root / "examples/input/reference_numbers.csv"),
        "--out", str(out),
    ])
    gate = read_json(out / "state/07_conflict_gate.json")
    assert len(gate["cases"]) > 0
