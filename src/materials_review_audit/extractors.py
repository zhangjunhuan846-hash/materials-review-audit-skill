from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import list_files, paragraphize, read_json, read_text, write_json


def build_inventory(
    manuscript_path: str | Path,
    figures_path: str | Path | None,
    source_data_dir: str | Path | None,
    database_path: str | Path | None,
    reference_numbers_path: str | Path | None,
    state_dir: str | Path,
) -> dict[str, Any]:
    text = read_text(manuscript_path)
    paragraphs = paragraphize(text)
    figures = read_json(figures_path, default=[]) if figures_path else []
    figure_mentions = sorted(set(re.findall(r"Fig(?:ure)?\.?\s*\d+[A-Za-z]?", text, flags=re.I)))
    table_mentions = sorted(set(re.findall(r"Table\s*\d+[A-Za-z]?", text, flags=re.I)))
    source_files = list_files(source_data_dir, ("*.csv", "*.xlsx", "*.xls")) if source_data_dir else []

    inventory = {
        "manuscript_path": str(manuscript_path),
        "paragraph_count": len(paragraphs),
        "paragraphs": paragraphs,
        "figure_manifest_path": str(figures_path) if figures_path else None,
        "figures": figures,
        "figure_mentions": figure_mentions,
        "table_mentions": table_mentions,
        "source_data_dir": str(source_data_dir) if source_data_dir else None,
        "source_data_files": source_files,
        "database_path": str(database_path) if database_path else None,
        "reference_numbers_path": str(reference_numbers_path) if reference_numbers_path else None,
    }
    write_json(Path(state_dir) / "01_inventory.json", inventory)
    return inventory
