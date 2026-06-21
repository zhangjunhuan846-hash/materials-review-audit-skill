from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import list_files, paragraphize, read_json, read_text, write_json


def normalize_figure_manifest(raw: Any) -> list[dict[str, Any]]:
    """Accept either a plain list or common dict-wrapped manifest formats."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in ("figures", "items", "manifest"):
            value = raw.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        # Single-figure manifest.
        if any(k in raw for k in ("figure_id", "id", "source_files", "expected_source_files")):
            return [raw]
    raise ValueError("figures_manifest.json must be a list of figure records or a dict containing a 'figures' list.")


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
    figures = normalize_figure_manifest(read_json(figures_path, default=[])) if figures_path else []
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
        "manifest_warnings": build_manifest_warnings(figures, figure_mentions),
    }
    write_json(Path(state_dir) / "01_inventory.json", inventory)
    return inventory


def build_manifest_warnings(figures: list[dict[str, Any]], figure_mentions: list[str]) -> list[dict[str, Any]]:
    manifest_ids = {str(f.get("figure_id") or f.get("id") or "").replace(" ", "") for f in figures}
    warnings: list[dict[str, Any]] = []
    for mention in figure_mentions:
        norm = mention.replace(" ", "")
        if manifest_ids and norm not in manifest_ids:
            warnings.append({"figure_mention": mention, "message": "figure mentioned in manuscript but not found in figures manifest"})
    return warnings
