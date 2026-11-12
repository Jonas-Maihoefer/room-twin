"""UUID-safe RoomPlan furniture replacement in an editable USD workspace."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path

from app.usd.catalog import AssetCatalog
from app.usd.matcher import ReplacementPlanItem, build_replacement_plan
from app.usd.scan_parser import RoomPlanScan
from app.usd.scan_parser import load_roomplan_scan
from app.usd.scene_reader import SceneInventory, read_usdz_inventory
from app.usd.transforms import TransformError, fit_bounds
from app.usd.workspace import extract_usdz


class ReplacementError(RuntimeError):
    """A selected object could not be replaced safely."""


@dataclass(frozen=True)
class ReplacementResult:
    workspace: Path
    root_layer: Path
    plan: tuple[ReplacementPlanItem, ...]
    warnings: tuple[str, ...]
    dependencies: tuple[Path, ...]


def _root_layer(workspace: Path) -> Path:
    from pxr import Usd
    for path in sorted(p for p in workspace.rglob("*") if p.suffix.lower() in {".usd", ".usda", ".usdc"}):
        stage = Usd.Stage.Open(str(path))
        if stage and stage.GetDefaultPrim() and any(p.GetMetadata("references") for p in stage.Traverse()):
            return path
    raise ReplacementError("extracted USDZ has no composed root layer")


def apply_replacements(usdz_path: str | Path, scan: RoomPlanScan, catalog: AssetCatalog,
                       inventory: SceneInventory, output_workspace: str | Path) -> ReplacementResult:
    """Compose scoped per-object overrides into a copied root layer.

    USD references in the RoomPlan root map each referenced layer's default
    prim into a distinct child below its category group. Editing that source
    default prim with added children would map those children onto the shared
    reference site. Overrides here target each composed UUID path instead, so
    instances remain isolated while source layers stay byte-for-byte intact.
    """
    from pxr import Gf, Usd, UsdGeom
    workspace = Path(output_workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    extract_usdz(usdz_path, workspace / "scene")
    root = _root_layer(workspace / "scene")
    stage = Usd.Stage.Open(str(root))
    if not stage:
        raise ReplacementError(f"cannot open extracted root stage {root}")
    plan = build_replacement_plan(scan, inventory, catalog)
    dependencies: list[Path] = []
    for item in plan:
        object_prims = [stage.GetPrimAtPath(path) for path in item.match.layer.composed_prim_paths]
        object_prims = [prim for prim in object_prims if prim]
        if len(object_prims) != 1:
            raise ReplacementError(f"expected one composed object prim for {item.match.uuid}, found {len(object_prims)}")
        obj = object_prims[0]
        # The UUID/category live on the referenced layer's default prim, while
        # the composition arc exposes the object through a child namespace.
        # Author identity at the exact composed object path for downstream tools.
        obj.SetCustomDataByKey("UUID", item.match.uuid)
        obj.SetCustomDataByKey("Category", item.match.source.category)
        if item.model is None:
            continue
        meshes = [prim for prim in Usd.PrimRange(obj) if prim.IsA(UsdGeom.Mesh)]
        if not meshes:
            raise ReplacementError(f"no placeholder mesh in composed object {obj.GetPath()}")

        local_bounds = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]).ComputeLocalBound(obj).ComputeAlignedRange()
        lo, hi = local_bounds.GetMin(), local_bounds.GetMax()
        ext = tuple(float(hi[i] - lo[i]) for i in range(3))
        if any(value <= 1e-8 for value in ext):
            raise ReplacementError(f"degenerate placeholder bounds for {item.match.uuid}: {ext}")
        target = item.match.source.dimensions

        dep = workspace / "scene" / "dependencies" / Path(*item.model.path.split("/"))
        dep.parent.mkdir(parents=True, exist_ok=True)
        if not dep.exists():
            shutil.copy2(catalog.root / item.model.path, dep)
        dependencies.append(dep)
        relative = Path(os.path.relpath(dep, root.parent)).as_posix()
        # The placeholder is itself an Imageable mesh prim in this scan. Hiding
        # it therefore hides every child, including a replacement. Put the new
        # model beside it and copy its local placement transform exactly once.
        replacement_path = obj.GetParent().GetPath().AppendChild(
            f"RoomTwinReplacement_{item.match.uuid.replace('-', '')}"
        )
        replacement = UsdGeom.Xform.Define(stage, replacement_path)
        replacement.GetPrim().SetCustomDataByKey("UUID", item.match.uuid)
        source_matrix = UsdGeom.Xformable(obj).GetLocalTransformation()
        UsdGeom.Xformable(replacement).AddTransformOp().Set(Gf.Matrix4d(source_matrix))
        # Keep the verified placeholder mesh's authored rotation and place the
        # fitted replacement at the placeholder's local-space bounds center.
        source_mesh = UsdGeom.Mesh(meshes[0])
        points = source_mesh.GetPointsAttr().Get() or []
        if not points:
            raise ReplacementError(f"placeholder mesh has no points for {item.match.uuid}")
        point_min = tuple(min(float(point[i]) for point in points) for i in range(3))
        point_max = tuple(max(float(point[i]) for point in points) for i in range(3))
        geometry_center = Gf.Vec3d(*((point_min[i] + point_max[i]) / 2 for i in range(3)))
        model_prim = UsdGeom.Xform.Define(stage, replacement.GetPath().AppendChild("Model"))
        model_prim.GetPrim().GetReferences().AddReference(relative)
        asset_stage = Usd.Stage.Open(str(dep))
        if not asset_stage:
            raise ReplacementError(f"cannot reopen copied model {dep}")
        if UsdGeom.GetStageUpAxis(asset_stage) != "Y":
            raise ReplacementError(f"catalog asset {item.model.path} is not Y-up; axis conversion is not configured")
        asset_meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(asset_stage))
        destination_meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage))
        if not (asset_meters_per_unit > 0 and asset_meters_per_unit < float("inf")):
            raise ReplacementError(f"catalog asset {item.model.path} has invalid metersPerUnit={asset_meters_per_unit}")
        if not (destination_meters_per_unit > 0 and destination_meters_per_unit < float("inf")):
            raise ReplacementError(f"destination stage has invalid metersPerUnit={destination_meters_per_unit}")
        default = asset_stage.GetDefaultPrim()
        if default:
            model_prim.GetPrim().GetReferences().ClearReferences()
            model_prim.GetPrim().GetReferences().AddReference(relative, default.GetPath())
        bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        asset_range = bbox.ComputeWorldBound(default or asset_stage.GetPseudoRoot()).ComputeAlignedRange()
        alo, ahi = asset_range.GetMin(), asset_range.GetMax()
        asset_ext = tuple(float(ahi[i] - alo[i]) for i in range(3))
        if any(value <= 1e-8 for value in asset_ext):
            raise ReplacementError(f"degenerate catalog bounds for {item.model.path}")
        try:
            # Referenced coordinates are composed verbatim; OpenUSD does not
            # rescale them based on the referenced layer's metersPerUnit. Fit
            # raw asset coordinates to destination-stage units exactly once.
            # The asset's unit metadata validates physical source dimensions,
            # while destination metersPerUnit converts RoomPlan metres.
            fitting = fit_bounds(tuple(float(alo[i]) for i in range(3)),
                                 tuple(float(ahi[i]) for i in range(3)),
                                 tuple(float(value) / destination_meters_per_unit for value in target))
        except TransformError as exc:
            raise ReplacementError(f"cannot fit catalog model {item.model.path}: {exc}") from exc
        scale, translation = fitting.scale, fitting.translation

        # Hide only original geometry. The sibling replacement does not inherit
        # the placeholder's visibility opinion.
        for mesh in meshes:
            UsdGeom.Imageable(mesh).MakeInvisible()
        xform = UsdGeom.Xformable(model_prim)
        local_target_center = Gf.Vec3d(*geometry_center)
        xform.AddTranslateOp().Set(Gf.Vec3d(*(translation[i] + local_target_center[i] for i in range(3))))
        xform.AddScaleOp().Set(Gf.Vec3f(*scale))
    stage.GetRootLayer().Save()

    final_stage = Usd.Stage.Open(str(root))
    if not final_stage:
        raise ReplacementError(f"edited root stage cannot reopen: {root}")
    for item in plan:
        if item.model is None:
            continue
        obj = final_stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])
        replacement_path = obj.GetParent().GetPath().AppendChild(
            f"RoomTwinReplacement_{item.match.uuid.replace('-', '')}"
        ) if obj else None
        replacement = final_stage.GetPrimAtPath(replacement_path) if replacement_path else None
        if not replacement or not any(prim.IsA(UsdGeom.Mesh) for prim in Usd.PrimRange(replacement)):
            raise ReplacementError(f"catalog geometry did not compose for UUID {item.match.uuid}")
    completed = tuple(dataclass_replace(item, status="replaced") if item.model else item for item in plan)
    return ReplacementResult(workspace, root, completed, (), tuple(sorted(set(dependencies))))


def process_roomplan(usdz_path: str | Path, json_path: str | Path, catalog: AssetCatalog,
                     output_workspace: str | Path, *, metadata_path: str | Path | None = None) -> ReplacementResult:
    """File-oriented library entry point for Issue C and non-API callers."""
    scan = load_roomplan_scan(json_path, metadata_path)
    inventory = read_usdz_inventory(usdz_path)
    return apply_replacements(usdz_path, scan, catalog, inventory, output_workspace)
