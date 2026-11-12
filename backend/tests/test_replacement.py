from pathlib import Path
import hashlib
import shutil
import pytest

from pxr import Usd, UsdGeom

from app.usd import AssetCatalog, load_roomplan_scan, process_roomplan, read_usdz_inventory

BACKEND = Path(__file__).parents[1]


def mesh_fingerprint(prim):
    mesh = UsdGeom.Mesh(prim)
    points = mesh.GetPointsAttr().Get()
    counts = mesh.GetFaceVertexCountsAttr().Get()
    indices = mesh.GetFaceVertexIndicesAttr().Get()
    data = repr((tuple(tuple(float(v) for v in p) for p in points or ()), tuple(counts or ()), tuple(indices or ())))
    return hashlib.sha256(data.encode()).hexdigest()


def mesh_map(stage, prefix):
    return {str(p.GetPath()): mesh_fingerprint(p) for p in stage.Traverse()
            if p.IsA(UsdGeom.Mesh) and p.GetPath().HasPrefix(prefix)}


def test_real_scan_replacements_are_composed_and_original_is_unchanged(tmp_path):
    source = BACKEND / "testdata/room.usdz"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    inventory = read_usdz_inventory(source)
    original_stage = Usd.Stage.Open(str(source))
    assert original_stage is not None
    arch_before = mesh_map(original_stage, "/room/Mesh_grp/Arch_grp")
    assert arch_before
    original_bounds = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    old_centers = {}
    for item in build_plan(scan, inventory):
        if item.model:
            old_range = original_bounds.ComputeLocalBound(original_stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])).ComputeAlignedRange()
            old_centers[item.match.uuid] = (old_range.GetMin() + old_range.GetMax()) / 2
    preserved_ids = {p.match.uuid for p in build_plan(scan, inventory) if not p.model}
    preserved_before = {}
    for item in build_plan(scan, inventory):
        if item.match.uuid in preserved_ids:
            root_prim = original_stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])
            preserved_before[item.match.uuid] = tuple(mesh_fingerprint(p) for p in Usd.PrimRange(root_prim) if p.IsA(UsdGeom.Mesh))
    standalone_assets = tmp_path / "standalone-assets"
    shutil.copytree(BACKEND / "assets", standalone_assets)
    standalone_catalog = AssetCatalog.load(standalone_assets / "catalog.json")
    result = process_roomplan(source, BACKEND / "testdata/room.json", standalone_catalog,
                             tmp_path / "editable", metadata_path=BACKEND / "testdata/metadata.json")
    assert len([p for p in result.plan if p.model]) == 6
    assert len([p for p in result.plan if not p.model]) == 2
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    stage = Usd.Stage.Open(str(result.root_layer))
    assert stage is not None
    assert len(result.dependencies) == 3
    assert mesh_map(stage, "/room/Mesh_grp/Arch_grp") == arch_before
    assert {p.match.uuid for p in result.plan if p.status == "replaced"} == {p.match.uuid for p in result.plan if p.model}
    for item in result.plan:
        root = stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])
        assert root
        if item.model:
            meshes = [p for p in Usd.PrimRange(root) if p.IsA(UsdGeom.Mesh)]
            assert meshes
            assert all(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible for m in meshes if m.GetName() != "RoomTwinReplacement")
            replacement = root.GetChild("RoomTwinReplacement")
            model_prim = replacement.GetChild("Model") if replacement else None
            assert replacement and model_prim and model_prim.HasAuthoredReferences()
            catalog_meshes = [p for p in Usd.PrimRange(replacement) if p.IsA(UsdGeom.Mesh)]
            assert catalog_meshes
            assert all(UsdGeom.Mesh(p).GetPointsAttr().Get() for p in catalog_meshes)
            assert root.GetCustomData().get("UUID", "").lower() == item.match.uuid
            assert root.GetCustomData().get("Category", "").lower() == item.match.source.category
            assert all(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible for m in meshes)
            local = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]).ComputeLocalBound(model_prim).ComputeAlignedRange()
            fitted = tuple(float(local.GetMax()[axis] - local.GetMin()[axis]) for axis in range(3))
            assert fitted == pytest.approx(item.match.source.dimensions, abs=0.002)
            local_range = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]).ComputeLocalBound(replacement).ComputeAlignedRange()
            local_center = (local_range.GetMin() + local_range.GetMax()) / 2
            assert tuple(float(local_center[i] - old_centers[item.match.uuid][i]) for i in range(3)) == pytest.approx((0, 0, 0), abs=0.002)
        else:
            assert root
            assert tuple(mesh_fingerprint(p) for p in Usd.PrimRange(root) if p.IsA(UsdGeom.Mesh)) == preserved_before[item.match.uuid]
    # Architectural references remain present and composed in the original hierarchy.
    assert len([p for p in stage.Traverse() if p.GetPath().HasPrefix("/room/Mesh_grp/Arch_grp")]) > 0
    used_layers = {Path(layer.identifier).resolve() for layer in stage.GetUsedLayers() if not layer.anonymous}
    assert set(result.dependencies).issubset(used_layers)


def build_plan(scan, inventory):
    from app.usd import build_replacement_plan
    return build_replacement_plan(scan, inventory, AssetCatalog.load())
