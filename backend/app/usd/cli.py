"""Offline command line for processing RoomPlan scans into USDZ."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from app.usd import AssetCatalog, process_roomplan
from app.usd.packaging import PackagingError, package_usdz, validate_usdz
from app.usd.publication import publish_output_pair


def _report(source: Path, output: Path, catalog: AssetCatalog, result, validation) -> dict:
    entries = []
    for item in result.plan:
        selected = item.model is not None
        reason = None
        if item.match_type == "category_default":
            reason = "category_fallback"
        elif not selected:
            same_category = any(model.category == item.match.source.category for model in catalog.models)
            reason = "no_compatible_attribute_match" if same_category else "no_matching_catalog_entry"
        entries.append({
            "uuid": item.match.uuid,
            "prim_path": item.match.layer.composed_prim_paths[0],
            "category": item.match.source.category,
            "status": item.status,
            "match_type": "exact" if item.match_type == "specific" else
                          "category_fallback" if item.match_type == "category_default" else "none",
            "attributes": dict(sorted((item.match.source.attributes or {}).items())),
            "model": item.model.path if item.model else None,
            "reason": reason,
        })
    entries.sort(key=lambda entry: entry["uuid"])
    replaced = sum(entry["status"] == "replaced" for entry in entries)
    return {
        "schema_version": "room-twin.replacement-report.v1",
        "source": source.name,
        "output": output.name,
        "catalog_version": catalog.catalog_version,
        "furniture_detected": len(entries),
        "furniture_replaced": replaced,
        "furniture_preserved": len(entries) - replaced,
        "objects": entries,
        "warnings": sorted(result.warnings),
        "validation": {"status": "passed" if validation.valid else "failed",
                       "root_layer": validation.root_layer,
                       "errors": list(validation.errors),
                       "geometry": validation.diagnostics["geometry"],
                       "package": validation.diagnostics["package"]},
        "package": validation.diagnostics["package"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.usd.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    replace = commands.add_parser("replace", help="replace recognized furniture and package a USDZ")
    replace.add_argument("--usdz", required=True, type=Path, help="source RoomPlan USDZ")
    replace.add_argument("--json", required=True, type=Path, help="RoomPlan JSON scan")
    replace.add_argument("--metadata", type=Path, help="optional RoomPlan metadata JSON")
    replace.add_argument("--catalog", type=Path,
                         default=Path(__file__).resolve().parents[2] / "assets" / "catalog.json",
                         help="asset catalog manifest (default: backend/assets/catalog.json)")
    replace.add_argument("--output", required=True, type=Path, help="destination .usdz path")
    replace.add_argument("--report", type=Path, help="report path (default: OUTPUT.report.json)")
    replace.add_argument("--force", action="store_true", help="replace existing output and report files")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source, scan_json = args.usdz.expanduser().resolve(), args.json.expanduser().resolve()
    metadata = args.metadata.expanduser().resolve() if args.metadata else None
    catalog_path = args.catalog.expanduser().resolve()
    output = args.output.expanduser().resolve()
    report_path = args.report.expanduser().resolve() if args.report else output.with_suffix(".report.json")

    input_paths = [(source, "source USDZ"), (scan_json, "RoomPlan JSON")]
    if metadata:
        input_paths.append((metadata, "metadata JSON"))
    for path, label in input_paths:
        if not path.is_file():
            print(f"error: {label} does not exist: {path}", file=sys.stderr)
            return 2
    if not catalog_path.is_file():
        print(f"error: catalog does not exist: {catalog_path}", file=sys.stderr)
        return 2
    if output.suffix.lower() != ".usdz":
        print("error: --output must end in .usdz", file=sys.stderr)
        return 2
    protected_inputs = {source, scan_json, catalog_path}
    if metadata:
        protected_inputs.add(metadata)
    if output == report_path or output in protected_inputs or report_path in protected_inputs:
        print("error: output/report paths must not overwrite any input", file=sys.stderr)
        return 2
    if not args.force and (output.exists() or report_path.exists()):
        print("error: output or report already exists (use --force to replace it)", file=sys.stderr)
        return 2

    workspace = None
    package_staging = None
    report_staging = None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        for destination in (output, report_path):
            if destination.exists() and not destination.is_file():
                raise OSError(f"output destination is not a regular file: {destination}")
        catalog = AssetCatalog.load(catalog_path)
        workspace = Path(tempfile.mkdtemp(prefix="room-twin-work-", dir=output.parent)) / "workspace"
        result = process_roomplan(source, scan_json, catalog, workspace, metadata_path=metadata)
        package_fd, staged_package_name = tempfile.mkstemp(
            prefix="room-twin-stage-", suffix=".usdz", dir=output.parent)
        os.close(package_fd)
        package_staging = Path(staged_package_name)
        package_staging.unlink()
        report_fd, staged_report_name = tempfile.mkstemp(
            prefix=f".{report_path.stem}.", suffix=".json", dir=report_path.parent)
        os.close(report_fd)
        report_staging = Path(staged_report_name)
        staged_output = package_staging
        staged_report = report_staging
        package_usdz(result, staged_output)
        validation = validate_usdz(staged_output, result)
        if not validation.valid:
            raise PackagingError("staged USDZ failed validation: " + "; ".join(validation.errors))
        report = _report(source, output, catalog, result, validation)
        staged_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        publish_output_pair(staged_output, staged_report, output, report_path, overwrite=args.force)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if workspace is not None:
            shutil.rmtree(workspace.parent, ignore_errors=True)
        for temporary in (package_staging, report_staging):
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    print("Room Twin processing complete")
    print(f"Furniture detected: {report['furniture_detected']}")
    print(f"Furniture replaced: {report['furniture_replaced']}")
    print(f"Furniture preserved: {report['furniture_preserved']}")
    print("USDZ validation: PASSED")
    print(f"Output: {output}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
