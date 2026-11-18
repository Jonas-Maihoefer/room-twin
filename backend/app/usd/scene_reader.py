"""Read-only USDZ inventory for Issue B's UUID-safe scene edits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from typing import Any


class SceneReadError(ValueError):
    """The USDZ could not be opened or inspected safely by OpenUSD."""


@dataclass(frozen=True)
class SourceLayer:
    layer_identifier: str
    asset_path: str
    category: str
    prim_paths: tuple[str, ...]
    composed_prim_paths: tuple[str, ...]
    uuids: tuple[str, ...]
    source_transforms: tuple[tuple[float, ...], ...]
    composed_transforms: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class SceneInventory:
    root_layer_identifier: str
    layer_identifiers: tuple[str, ...]
    up_axis: str
    meters_per_unit: float
    stage_metadata: Mapping[str, Any]
    references: tuple[SourceLayer, ...]
    furniture_layers: tuple[SourceLayer, ...]
    architectural_layers: tuple[SourceLayer, ...]
    architectural_groups: tuple[str, ...]


def _category_from_path(prim_path: str, asset_path: str) -> str:
    leaf = Path(asset_path).stem.lower()
    if leaf.startswith("door"):
        return "door"
    if leaf.startswith("window"):
        return "window"
    if leaf.startswith("wall"):
        return "wall"
    if leaf.startswith("floor"):
        return "floor"
    parts = prim_path.split("/")
    for part in reversed(parts):
        if part.endswith("_grp"):
            return part[:-4].lower()
    return "unknown"


def read_usdz_inventory(path: str | Path) -> SceneInventory:
    """Open a USDZ with OpenUSD and return a stable layer/reference inventory.

    The package is opened in place through OpenUSD's USDZ resolver; this reader
    does not extract or modify the archive. Multiple reference items beneath a
    shared category prim are recorded individually.
    """
    source = Path(path).resolve()
    if not source.is_file() or source.suffix.lower() != ".usdz":
        raise SceneReadError(f"USDZ file does not exist: {source}")
    try:
        from pxr import Sdf, Usd, UsdGeom
        stage = Usd.Stage.Open(str(source))
    except Exception as exc:
        raise SceneReadError(f"OpenUSD could not open {source}: {exc}") from exc
    if stage is None:
        raise SceneReadError(f"OpenUSD could not open {source}")
    root = stage.GetRootLayer()
    if root is None or not root.identifier:
        raise SceneReadError("USDZ has no root layer")

    # GetUsedLayers includes the ephemeral session layer; only authored package
    # layers count toward the stable source inventory.
    def stable_layer_identifier(identifier: str) -> str:
        if identifier == root.identifier:
            return source.name
        if "[" in identifier and identifier.endswith("]"):
            return f"{source.name}[{identifier.rsplit('[', 1)[1][:-1]}]"
        return Path(identifier).name

    layer_ids = tuple(sorted({stable_layer_identifier(layer.identifier)
                              for layer in stage.GetUsedLayers() if not layer.anonymous}))
    records: list[SourceLayer] = []
    for prim in stage.Traverse():
        ref_list = prim.GetMetadata("references")
        if not ref_list:
            continue
        refs = tuple(ref_list.GetAddedOrExplicitItems())
        for ref in refs:
            asset_path = str(ref.assetPath).replace("\\", "/").removeprefix("./")
            package_identifier = f"{root.identifier}[{asset_path}]"
            try:
                layer = Sdf.Layer.FindOrOpen(package_identifier)
            except Exception as exc:
                raise SceneReadError(f"cannot open referenced layer {asset_path}: {exc}") from exc
            if layer is None:
                raise SceneReadError(f"cannot open referenced layer {asset_path}")
            try:
                substage = Usd.Stage.Open(layer)
            except Exception as exc:
                raise SceneReadError(f"cannot inspect referenced layer {asset_path}: {exc}") from exc
            prim_paths: list[str] = []
            uuids: list[str] = []
            transforms: list[tuple[float, ...]] = []
            composed_paths: list[str] = []
            composed_transforms: list[tuple[float, ...]] = []
            reference_prim_name = Path(asset_path).stem
            for child in prim.GetChildren():
                if child.GetName() != reference_prim_name:
                    continue
                composed_paths.append(str(child.GetPath()))
                xform = UsdGeom.Xformable(child)
                matrix = xform.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
                composed_transforms.append(tuple(float(matrix[i][j]) for i in range(4) for j in range(4)))
            if substage:
                for subprim in substage.Traverse():
                    prim_paths.append(str(subprim.GetPath()))
                    custom_data: dict[str, Any] = dict(subprim.GetCustomData())
                    identity = custom_data.get("UUID") or custom_data.get("uuid") or custom_data.get("identifier")
                    if identity is not None:
                        uuids.append(str(identity))
                    try:
                        xform = UsdGeom.Xformable(subprim)
                        if xform:
                            matrix = xform.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
                            transforms.append(tuple(float(matrix[i][j]) for i in range(4) for j in range(4)))
                    except Exception as exc:
                        raise SceneReadError(f"cannot read transform at {asset_path}:{subprim.GetPath()}: {exc}") from exc
            records.append(SourceLayer(
                f"{source.name}[{asset_path}]",
                asset_path,
                _category_from_path(str(prim.GetPath()), asset_path),
                tuple(sorted(prim_paths)),
                tuple(sorted(composed_paths)),
                tuple(sorted(set(uuids))),
                tuple(transforms),
                tuple(composed_transforms),
            ))
    records.sort(key=lambda item: item.asset_path)
    architecture = tuple(record for record in records if record.category in {"wall", "floor", "door", "window"})
    furniture = tuple(record for record in records if record not in architecture)
    groups = tuple(sorted(str(prim.GetPath()) for prim in stage.Traverse()
                          if prim.GetPath().name.endswith("_grp") and
                          any(key in str(prim.GetPath()).lower() for key in ("arch", "floor", "object"))))
    return SceneInventory(
        source.name, layer_ids, UsdGeom.GetStageUpAxis(stage),
        float(UsdGeom.GetStageMetersPerUnit(stage)),
        {
            "default_prim": str(stage.GetDefaultPrim().GetPath()) if stage.GetDefaultPrim() else None,
            "start_time_code": float(stage.GetStartTimeCode()),
            "end_time_code": float(stage.GetEndTimeCode()),
            "time_codes_per_second": float(stage.GetTimeCodesPerSecond()),
            "frames_per_second": float(stage.GetFramesPerSecond()),
            "up_axis": UsdGeom.GetStageUpAxis(stage),
            "meters_per_unit": float(UsdGeom.GetStageMetersPerUnit(stage)),
            "custom_layer_data": dict(root.customLayerData),
        }, tuple(records), furniture,
        architecture, groups,
    )
