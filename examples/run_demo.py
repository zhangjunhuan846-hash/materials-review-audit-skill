from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from materials_review_audit.cli import main

main([
    "audit",
    "--manuscript", str(ROOT / "examples/input/manuscript_excerpt.md"),
    "--figures", str(ROOT / "examples/input/figures_manifest.json"),
    "--source-data-dir", str(ROOT / "examples/input/source_data"),
    "--database", str(ROOT / "examples/input/databases/descriptor_database.csv"),
    "--reference-numbers", str(ROOT / "examples/input/reference_numbers.csv"),
    "--out", str(ROOT / "outputs/demo_audit"),
])
