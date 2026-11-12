"""USDZ packaging and independent OpenUSD validation."""
from __future__ import annotations

import os
import math
import tempfile
import zipfile
from dataclasses import dataclass, field
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
    diagnostics: dict = field(default_factory=dict)


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
    diagnostics = {
        "geometry": {
            "status": "not_performed",
            "architecture_preserved": {"status": "not_performed"},
            "object_count_preserved": {"status": "not_performed"},
            "replacement_geometry_valid": {"status": "not_performed"},
            "transforms": {"status": "not_performed"},
            "warnings": [],
            "errors": [],
        },
        "package": {
            "status": "not_performed",
            "file_count": 0,
            "files": [],
            "usd_layers": [],
            "replacement_assets": [],
            "external_dependencies_detected": None,
            "unresolved_dependencies": [],
        },
    }
    try:
        root_member = _root_member(package)
        with zipfile.ZipFile(package) as archive:
            package_files = [name for name in archive.namelist() if not name.endswith("/")]
        diagnostics["package"].update({
            "file_count": len(package_files),
            "files": sorted(package_files),
            "usd_layers": sorted(name for name in package_files
                                 if name.lower().endswith((".usd", ".usda", ".usdc"))),
            "root_layer": root_member,
        })
        stage = Usd.Stage.Open(str(package))
        if not stage:
            return ValidationResult(False, root_member, ("OpenUSD could not open the packaged stage",))
        default_prim = stage.GetDefaultPrim()
        if not default_prim or not default_prim.IsValid():
            errors.append("packaged stage has no valid default prim")

        _, assets, unresolved = UsdUtils.ComputeAllDependencies(Sdf.AssetPath(stage.GetRootLayer().identifier))
        diagnostics["package"]["unresolved_dependencies"] = sorted(set(unresolved))
        diagnostics["package"]["external_dependencies_detected"] = bool(unresolved)
        if unresolved:
            errors.extend(f"unresolved dependency: {asset}" for asset in sorted(set(unresolved)))

        # Dependency discovery catches unresolved arcs; the fresh stage traversal
        # confirms every replacement is composed and carries actual mesh points.
        if result is not None:
            all_present = True
            replacement_geometry_valid = True
            replacement_assets = set()
            transform_results = []
            bounds_results = []
            xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
            for item in result.plan:
                object_path = item.match.layer.composed_prim_paths[0]
                obj = stage.GetPrimAtPath(object_path)
                if not obj:
                    errors.append(f"source furniture prim missing for UUID {item.match.uuid}")
                    all_present = False
                    continue
                if obj.GetCustomData().get("UUID", "").lower() != item.match.uuid:
                    errors.append(f"UUID identity not retained for {item.match.uuid}")
                if item.model is None:
                    meshes = [p for p in Usd.PrimRange(obj) if p.IsA(UsdGeom.Mesh)]
                    if not meshes or any(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible for m in meshes):
                        errors.append(f"preserved placeholder geometry is unavailable for {item.match.uuid}")
                    continue
                replacement_assets.add(item.model.path)
                replacement_path = obj.GetParent().GetPath().AppendChild(
                    f"RoomTwinReplacement_{item.match.uuid.replace('-', '')}")
                replacement = stage.GetPrimAtPath(replacement_path)
                meshes = [p for p in Usd.PrimRange(replacement) if p.IsA(UsdGeom.Mesh)] if replacement else []
                mesh_points = [point for mesh in meshes
                               for point in (UsdGeom.Mesh(mesh).GetPointsAttr().Get() or ())]
                finite_points = all(all(math.isfinite(float(value)) for value in point)
                                    for point in mesh_points)
                if not meshes or not mesh_points or not finite_points:
                    errors.append(f"replacement mesh did not compose for UUID {item.match.uuid}")
                    replacement_geometry_valid = False
                if any(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible for m in meshes):
                    errors.append(f"replacement geometry is invisible for UUID {item.match.uuid}")
                    replacement_geometry_valid = False
                if replacement:
                    matrix = xform_cache.GetLocalToWorldTransform(replacement)
                    transform = [float(matrix[r][c]) for r in range(4) for c in range(4)]
                    transform_ok = all(math.isfinite(value) for value in transform)
                    transform_results.append({"uuid": item.match.uuid, "status":
                                              "passed" if transform_ok else "failed"})
                    bound = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]) \
                        .ComputeWorldBound(replacement).ComputeAlignedRange()
                    low, high = bound.GetMin(), bound.GetMax()
                    bbox = [[float(low[i]), float(high[i])] for i in range(3)]
                    bbox_ok = all(math.isfinite(v) for axis in bbox for v in axis) and all(
                        axis[1] > axis[0] for axis in bbox)
                    bounds_results.append({"uuid": item.match.uuid, "status":
                                           "passed" if bbox_ok else "failed", "world_bounds": bbox})
                    if not transform_ok or not bbox_ok:
                        errors.append(f"invalid transform or world bounds for replacement {item.match.uuid}")

            diagnostics["geometry"]["object_count_preserved"] = {
                "status": "passed" if all_present else "failed",
                "expected": len(result.plan),
                "actual": sum(bool(stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0]))
                              for item in result.plan),
            }
            diagnostics["geometry"]["replacement_geometry_valid"] = {
                "status": "passed" if replacement_geometry_valid else "failed",
                "replacements_checked": sum(item.model is not None for item in result.plan),
            }
            diagnostics["package"]["replacement_assets"] = sorted(
                asset for asset in replacement_assets
                if any(member.endswith(Path(asset).name) for member in package_files)
            )
            missing_assets = sorted(replacement_assets - set(diagnostics["package"]["replacement_assets"]))
            if missing_assets:
                errors.extend(f"replacement asset is not present in package: {asset}" for asset in missing_assets)

            def architecture_signature(arch_stage):
                signature = []
                for prim in arch_stage.Traverse():
                    if not prim.IsA(UsdGeom.Mesh):
                        continue
                    if "arch_grp" not in str(prim.GetPath()).lower():
                        continue
                    mesh = UsdGeom.Mesh(prim)
                    signature.append((str(prim.GetPath()),
                                      tuple(tuple(float(v) for v in point)
                                            for point in (mesh.GetPointsAttr().Get() or ())),
                                      tuple(mesh.GetFaceVertexCountsAttr().Get() or ()),
                                      tuple(mesh.GetFaceVertexIndicesAttr().Get() or ())))
                return tuple(sorted(signature))

            source_stage = Usd.Stage.Open(str(result.root_layer))
            if source_stage:
                expected_architecture = architecture_signature(source_stage)
                actual_architecture = architecture_signature(stage)
                arch_ok = bool(expected_architecture) and expected_architecture == actual_architecture
                diagnostics["geometry"]["architecture_preserved"] = {
                    "status": "passed" if arch_ok else "failed" if expected_architecture else "not_performed",
                    "mesh_count": len(actual_architecture),
                }
                if expected_architecture and not arch_ok:
                    errors.append("architectural geometry differs from the processed source scene")
            else:
                diagnostics["geometry"]["architecture_preserved"] = {"status": "not_performed"}
            diagnostics["geometry"]["transforms"] = {
                "status": "passed" if all_present and all(
                    entry["status"] == "passed" for entry in transform_results + bounds_results) else "failed",
                "objects_checked": len(result.plan),
                "replacement_transforms": transform_results,
                "replacement_world_bounds": bounds_results,
            }
            diagnostics["geometry"]["status"] = (
                "passed" if all(diagnostics["geometry"][key]["status"] == "passed" for key in
                                ("architecture_preserved", "object_count_preserved",
                                 "replacement_geometry_valid", "transforms")) else "failed"
            )

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
        external_assets = []
        for asset in assets:
            normalized_asset = asset.replace("\\", "/").casefold()
            in_package = normalized_asset == normalized_package or normalized_asset.startswith(normalized_package + "[")
            if os.path.isabs(asset) and not in_package:
                external_assets.append(asset)
                errors.append(f"dependency resolves outside the package: {asset}")
        diagnostics["package"]["external_dependencies_detected"] = bool(unresolved or external_assets)
        diagnostics["package"]["external_dependencies"] = sorted(set(external_assets))

        diagnostics["package"]["dependency_resolution"] = (
            "passed" if not unresolved and not external_assets else "failed"
        )
        diagnostics["package"]["status"] = diagnostics["package"]["dependency_resolution"]
        diagnostics["geometry"]["errors"] = list(errors)
        return ValidationResult(not errors, root_member, tuple(errors), (), diagnostics)
    except Exception as exc:  # OpenUSD may raise native exceptions for broken packages.
        diagnostics["package"]["status"] = "failed"
        diagnostics["geometry"]["status"] = "failed"
        diagnostics["geometry"]["errors"] = [f"USDZ validation failed: {exc}"]
        return ValidationResult(False, None, (f"USDZ validation failed: {exc}",), (), diagnostics)


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
