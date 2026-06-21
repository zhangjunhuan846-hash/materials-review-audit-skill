from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_text(path: str | Path) -> str:
    p = Path(path)
    if p.suffix.lower() == ".docx":
        try:
            import docx  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Reading .docx requires python-docx. Install it or provide .md/.txt.") from exc
        doc = docx.Document(str(p))
        return "\n".join(par.text for par in doc.paragraphs)
    return p.read_text(encoding="utf-8", errors="ignore")


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_csv(path: str | Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for k in row.keys():
                if k not in keys:
                    keys.append(k)
        fieldnames = keys or ["empty"]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: stringify(row.get(k, "")) for k in fieldnames})


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def stringify(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def split_sentences(text: str) -> list[str]:
    # Conservative sentence splitter for English/Chinese punctuation.
    parts = re.split(r"(?<=[.!?。！？])\s+|(?<=[。！？])", text)
    return [p.strip() for p in parts if p and p.strip()]


def paragraphize(text: str) -> list[dict[str, Any]]:
    paragraphs: list[dict[str, Any]] = []
    section = "front_matter"
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            section = line.lstrip("#").strip() or section
        paragraphs.append({
            "paragraph_id": f"P{i:04d}",
            "section": section,
            "text": line,
            "char_count": len(line),
            "approx_tokens": max(1, len(line) // 4),
        })
    return paragraphs


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def safe_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none", "na", "n/a", "-"}:
        return None
    m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def list_files(path: str | Path, patterns: Iterable[str] = ("*",)) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    files: list[Path] = []
    for pattern in patterns:
        files.extend(p.rglob(pattern))
    return sorted(str(f.relative_to(p)) for f in files if f.is_file())
