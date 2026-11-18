"""Failure-safe publication of the related USDZ and JSON report files."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


class PublicationError(OSError):
    """The output pair could not be published consistently."""


def _backup_path(path: Path) -> Path:
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".backup", dir=path.parent)
    os.close(fd)
    Path(name).unlink()
    return Path(name)


def publish_output_pair(staged_usdz: Path, staged_report: Path, output: Path,
                        report: Path, *, overwrite: bool) -> None:
    """Publish two validated files and restore old files on ordinary failures.

    This is rollback-safe for handled filesystem errors; it is not a crash-proof
    multi-file transaction.
    """
    staged_usdz, staged_report = Path(staged_usdz), Path(staged_report)
    output, report = Path(output), Path(report)
    if output == report or output.resolve() == report.resolve():
        raise PublicationError("USDZ and report destinations must be different")
    for staged in (staged_usdz, staged_report):
        if not staged.is_file():
            raise PublicationError(f"staged artifact is missing: {staged}")
    for destination in (output, report):
        if not destination.parent.is_dir():
            raise PublicationError(f"output directory does not exist: {destination.parent}")
        if destination.exists() and not destination.is_file():
            raise PublicationError(f"output destination is not a regular file: {destination}")
    existing = [path for path in (output, report) if path.exists()]
    if existing and not overwrite:
        raise PublicationError(f"output or report already exists (use --force to replace it): {existing[0]}")

    backups: dict[Path, Path] = {}
    published: list[Path] = []
    preserve_backups = False
    try:
        for destination in existing:
            backup = _backup_path(destination)
            backups[destination] = backup
            os.replace(destination, backup)
        if overwrite:
            os.replace(staged_usdz, output)
            published.append(output)
        else:
            os.link(staged_usdz, output)
            published.append(output)
            staged_usdz.unlink()
        if overwrite:
            os.replace(staged_report, report)
            published.append(report)
        else:
            os.link(staged_report, report)
            published.append(report)
            staged_report.unlink()
    except Exception as exc:
        rollback_errors = []
        for destination in reversed(published):
            try:
                destination.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"{destination}: {rollback_exc}")
        for destination, backup in backups.items():
            if backup.exists():
                try:
                    os.replace(backup, destination)
                except OSError as rollback_exc:
                    rollback_errors.append(f"{destination}: {rollback_exc}")
        preserve_backups = bool(rollback_errors)
        detail = f"; rollback errors: {'; '.join(rollback_errors)}" if rollback_errors else ""
        raise PublicationError(f"could not publish output pair: {exc}{detail}") from exc
    finally:
        if not preserve_backups:
            for backup in backups.values():
                backup.unlink(missing_ok=True)
