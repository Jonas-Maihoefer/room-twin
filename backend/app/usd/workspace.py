"""Prepare a bounded, path-safe editable copy of a USDZ package."""
from __future__ import annotations

import zipfile
from pathlib import Path, PurePosixPath


class WorkspaceError(ValueError):
    pass


MAX_UNPACKED = 2 * 1024 * 1024 * 1024


def extract_usdz(source: str | Path, destination: str | Path) -> Path:
    source, destination = Path(source), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            seen: set[str] = set()
            total = 0
            root_candidate = None
            for info in infos:
                raw = info.filename.replace("\\", "/")
                path = PurePosixPath(raw)
                key = str(path).casefold()
                mode = (info.external_attr >> 16) & 0xFFFF
                if (path.is_absolute() or not path.parts or "\x00" in raw
                        or any(part in {"..", "."} or ":" in part for part in path.parts)):
                    raise WorkspaceError(f"unsafe USDZ entry path: {info.filename!r}")
                if key in seen:
                    raise WorkspaceError(f"duplicate or colliding USDZ entry: {info.filename!r}")
                seen.add(key)
                if root_candidate is None and not info.is_dir() and path.suffix.lower() in {".usd", ".usda", ".usdc"}:
                    root_candidate = destination.joinpath(*path.parts)
                if mode and mode & 0o170000 not in {0, 0o040000, 0o100000}:
                    raise WorkspaceError(f"unsupported USDZ entry type: {info.filename!r}")
                total += info.file_size
                if total > MAX_UNPACKED:
                    raise WorkspaceError("USDZ expands beyond the 2 GiB safety limit")
                if info.file_size > 1024 * 1024 and info.compress_size and info.file_size / info.compress_size > 1000:
                    raise WorkspaceError(f"unreasonable compression ratio in {info.filename!r}")
            for info in infos:
                target = destination.joinpath(*PurePosixPath(info.filename.replace("\\", "/")).parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as src, target.open("xb") as dst:
                        while chunk := src.read(1024 * 1024):
                            dst.write(chunk)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        raise WorkspaceError(f"cannot safely extract USDZ {source}: {exc}") from exc
    if root_candidate is None or not root_candidate.is_file():
        raise WorkspaceError("USDZ contains no supported USD layers")
    return root_candidate
