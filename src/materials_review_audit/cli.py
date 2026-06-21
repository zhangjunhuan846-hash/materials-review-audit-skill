from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .claims import build_claim_ledger
from .conflict_gate import build_conflict_gate
from .context_pack import build_context_pack
from .descriptors import audit_descriptor_database
from .extractors import build_inventory
from .figures import audit_figure_text
from .numbers import build_number_ledger
from .report import flatten_findings, write_report
from .source_data import build_source_data_ledger
from .utils import ensure_dir


def _check_optional_file(path: Path | None, label: str) -> None:
    if path is not None and not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")


def run_audit(args: argparse.Namespace) -> dict:
    if not args.manuscript.exists():
        raise FileNotFoundError(f"manuscript not found: {args.manuscript}")
    _check_optional_file(args.figures, "figures manifest")
    _check_optional_file(args.database, "descriptor database")
    _check_optional_file(args.reference_numbers, "reference numbers")
    if args.source_data_dir is not None and not args.source_data_dir.exists():
        raise FileNotFoundError(f"source-data directory not found: {args.source_data_dir}")

    out_dir = ensure_dir(args.out)
    state_dir = ensure_dir(out_dir / "state")

    inventory = build_inventory(args.manuscript, args.figures, args.source_data_dir, args.database, args.reference_numbers, state_dir)
    context_pack = build_context_pack(inventory, args.reference_numbers, state_dir)
    number_ledger = build_number_ledger(context_pack["selected_context"], args.reference_numbers, out_dir, state_dir)
    claim_ledger = build_claim_ledger(context_pack["selected_context"], out_dir, state_dir)
    source_ledger = build_source_data_ledger(inventory.get("figures", []), args.source_data_dir, out_dir, state_dir)
    descriptor_audit = audit_descriptor_database(args.database, out_dir, state_dir)
    figure_text = audit_figure_text(claim_ledger, source_ledger, args.source_data_dir, out_dir, state_dir)
    findings = flatten_findings(number_ledger, claim_ledger, source_ledger, descriptor_audit, figure_text)
    conflict_gate = build_conflict_gate(findings, out_dir, state_dir)
    result = write_report(out_dir, findings, source_ledger, conflict_gate)
    print(f"Audit complete: {out_dir}")
    print(f"Report: {out_dir / 'audit_report.md'}")
    print(f"Decision: {result['readiness']} | counts={result['counts']}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="materials-review-audit", description="Audit materials review manuscript packages.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="Run a manuscript/source-data/database consistency audit.")
    audit.add_argument("--manuscript", required=True, type=Path)
    audit.add_argument("--figures", required=False, type=Path, help="Path to figures_manifest.json")
    audit.add_argument("--source-data-dir", required=False, type=Path)
    audit.add_argument("--database", required=False, type=Path, help="Descriptor database .csv/.xlsx")
    audit.add_argument("--reference-numbers", required=False, type=Path)
    audit.add_argument("--out", required=True, type=Path)
    audit.set_defaults(func=run_audit)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return None


if __name__ == "__main__":
    main()
