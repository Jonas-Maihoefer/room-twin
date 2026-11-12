"""USDZ packaging and independent OpenUSD validation."""
from __future__ import annotations

import os
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
import shutil

from app.usd.replacement import ReplacementResult


class PackagingError(RuntimeError):
    """A USDZ could not be safely created or validated."""


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    root_layer: str | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def _root_member(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if name.lower().endswith((".usd", ".usda", ".usdc"))]
            if not members:
                raise PackagingError("USDZ contains no USD root layer")
            return members[0]
    except (OSError, zipfile.BadZipFile) as exc:
        raise PackagingError(f"cannot inspect USDZ package {path}: {exc}") from exc


def validate_usdz(path: str | Path, result: ReplacementResult | None = None) -> ValidationResult:
    """Reopen a package and check composition, dependencies and replacements."""
    from pxr import Sdf, Usd, UsdGeom, UsdUtils

    package = Path(path).resolve()
    errors: list[str] = []
    try:
        root_member = _root_member(package)
        stage = Usd.Stage.Open(str(package))
        if not stage:
            return ValidationResult(False, root_member, ("OpenUSD could not open the packaged stage",))
        default_prim = stage.GetDefaultPrim()
        if not default_prim or not default_prim.IsValid():
            errors.append("packaged stage has no valid default prim")

        _, assets, unresolved = UsdUtils.ComputeAllDependencies(Sdf.AssetPath(stage.GetRootLayer().identifier))
        if unresolved:
            errors.extend(f"unresolved dependency: {asset}" for asset in sorted(set(unresolved)))

        # Dependency discovery catches unresolved arcs; the fresh stage traversal
        # confirms every replacement is composed and carries actual mesh points.
        if result is not None:
            for item in result.plan:
                object_path = item.match.layer.composed_prim_paths[0]
                obj = stage.GetPrimAtPath(object_path)
                if not obj:
                    errors.append(f"source furniture prim missing for UUID {item.match.uuid}")
                    continue
                if obj.GetCustomData().get("UUID", "").lower() != item.match.uuid:
                    errors.append(f"UUID identity not retained for {item.match.uuid}")
                if item.model is None:
                    meshes = [p for p in Usd.PrimRange(obj) if p.IsA(UsdGeom.Mesh)]
                    if not meshes or any(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible for m in meshes):
                        errors.append(f"preserved placeholder geometry is unavailable for {item.match.uuid}")
                    continue
                replacement_path = obj.GetParent().GetPath().AppendChild(
                    f"RoomTwinReplacement_{item.match.uuid.replace('-', '')}")
                replacement = stage.GetPrimAtPath(replacement_path)
                meshes = [p for p in Usd.PrimRange(replacement) if p.IsA(UsdGeom.Mesh)] if replacement else []
                if not meshes or not any(UsdGeom.Mesh(m).GetPointsAttr().Get() for m in meshes):
                    errors.append(f"replacement mesh did not compose for UUID {item.match.uuid}")
                if any(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible for m in meshes):
                    errors.append(f"replacement geometry is invisible for UUID {item.match.uuid}")

        # A packaged stage must resolve via package-relative paths. Reject any
        # file-backed used layer outside the USDZ; package layer identifiers use
        # the `package[member]` form and are allowed.
        normalized_package = str(package).replace("\\", "/").casefold()
        for layer in stage.GetUsedLayers():
            identifier = layer.identifier
            normalized_identifier = identifier.replace("\\", "/").casefold()
            if "[" in normalized_identifier and normalized_identifier.startswith(normalized_package + "["):
                continue
            if identifier.startswith("anon:"):
                continue
            if os.path.isabs(identifier) and Path(identifier).resolve() != package:
                errors.append(f"stage uses external absolute layer: {identifier}")
        for asset in assets:
            normalized_asset = asset.replace("\\", "/").casefold()
            in_package = normalized_asset == normalized_package or normalized_asset.startswith(normalized_package + "[")
            if os.path.isabs(asset) and not in_package:
                errors.append(f"dependency resolves outside the package: {asset}")

        return ValidationResult(not errors, root_member, tuple(errors))
    except Exception as exc:  # OpenUSD may raise native exceptions for broken packages.
        return ValidationResult(False, None, (f"USDZ validation failed: {exc}",))


def package_usdz(result: ReplacementResult, output_path: str | Path, *, overwrite: bool = False) -> Path:
    """Package a processed scene atomically using OpenUSD's USDZ writer.

    Existing outputs are preserved unless ``overwrite`` is explicit. The
    caller owns ``result.workspace`` and can retain or remove it independently.
    """
    from pxr import Sdf, UsdUtils

    output = Path(output_path).expanduser().resolve()
    if output.suffix.lower() != ".usdz":
        raise PackagingError("output path must end in .usdz")
    if not result.root_layer.is_file():
        raise PackagingError(f"processed root layer does not exist: {result.root_layer}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PackagingError(f"cannot create output directory {output.parent}: {exc}") from exc
    if output.exists() and not overwrite:
        raise PackagingError(f"output already exists (pass overwrite=True to replace it): {output}")

    try:
        staging_dir = Path(tempfile.mkdtemp(prefix="room-twin-package-", dir=output.parent))
    except OSError as exc:
        raise PackagingError(f"cannot create temporary package in {output.parent}: {exc}") from exc
    temporary = staging_dir / f"{output.stem}.tmp.usdz"
    try:
        # Establish the resolver context for the edited root before dependency
        # traversal. CreateNewUsdzPackage localizes references and dependencies.
        root = str(result.root_layer.resolve())
        context = _resolver_context(root)
        with context:
            created = UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(root), str(temporary))
        if not created or not temporary.is_file() or temporary.stat().st_size == 0:
            raise PackagingError("OpenUSD did not create a complete USDZ package")
        validation = validate_usdz(temporary, result)
        if not validation.valid:
            raise PackagingError("packaged USDZ failed validation: " + "; ".join(validation.errors))
        if overwrite:
            os.replace(temporary, output)
        else:
            try:
                os.link(temporary, output)
            except FileExistsError as exc:
                raise PackagingError(f"output appeared during packaging: {output}") from exc
            temporary.unlink()
        return output
    except PackagingError:
        raise
    except Exception as exc:
        raise PackagingError(f"OpenUSD packaging failed for {result.root_layer}: {exc}") from exc
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


def _resolver_context(root: str):
    """Return a bound resolver context for the root layer's directory."""
    from pxr import Ar
    return Ar.ResolverContextBinder(Ar.GetResolver().CreateDefaultContextForAsset(root))
