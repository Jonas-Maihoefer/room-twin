from pathlib import Path
import hashlib
import shutil

import pytest
from pxr import Gf, Usd, UsdGeom

from app.usd import AssetCatalog, load_roomplan_scan, process_roomplan, read_usdz_inventory
from app.usd.catalog import CatalogModel

BACKEND = Path(__file__).parents[1]
TOLERANCE_METRES = 0.002
WORLD_POSITION_TOLERANCE_METRES = 0.002


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


def world_xform_map(stage, prefix):
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    return {str(p.GetPath()): tuple(float(cache.GetLocalToWorldTransform(p)[i][j])
                                    for i in range(4) for j in range(4))
            for p in stage.Traverse() if p.GetPath().HasPrefix(prefix)}


def replacement_for(stage, item):
    obj = stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])
    assert obj
    path = obj.GetParent().GetPath().AppendChild(
        f"RoomTwinReplacement_{item.match.uuid.replace('-', '')}"
    )
    return obj, stage.GetPrimAtPath(path)


def composed_mesh_bounds(meshes, xform_cache, *, frame_inverse=None):
    """Bound composed vertices after transforming them into the requested frame."""
    points = []
    for mesh_prim in meshes:
        mesh = UsdGeom.Mesh(mesh_prim)
        matrix = xform_cache.GetLocalToWorldTransform(mesh_prim)
        for point in mesh.GetPointsAttr().Get() or ():
            world_point = matrix.Transform(Gf.Vec3d(point))
            points.append(frame_inverse.Transform(world_point) if frame_inverse else world_point)
    assert points
    lo = Gf.Vec3d(*(min(float(point[axis]) for point in points) for axis in range(3)))
    hi = Gf.Vec3d(*(max(float(point[axis]) for point in points) for axis in range(3)))
    return lo, hi


def assert_matrix_pose_equal(actual, expected, tolerance=TOLERANCE_METRES):
    # Rotation basis is compared separately from bounds, so yaw cannot be
    # mistaken for a size or placement error.
    for row in range(3):
        for column in range(3):
            assert float(actual[row][column]) == pytest.approx(float(expected[row][column]), abs=tolerance)
    for column in range(3):
        assert float(actual[3][column]) == pytest.approx(float(expected[3][column]), abs=tolerance)


def test_real_scan_replacements_are_visible_and_preserve_world_placement(tmp_path):
    source = BACKEND / "testdata/room.usdz"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    inventory = read_usdz_inventory(source)
    original_stage = Usd.Stage.Open(str(source))
    assert original_stage is not None
    arch_before = mesh_map(original_stage, "/room/Mesh_grp/Arch_grp")
    assert arch_before
    arch_xforms_before = world_xform_map(original_stage, "/room/Mesh_grp/Arch_grp")
    original_xforms = UsdGeom.XformCache(Usd.TimeCode.Default())
    plan = build_plan(scan, inventory)
    old_poses, preserved_before = {}, {}
    for item in plan:
        obj = original_stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])
        assert obj
        if item.model:
            original_meshes = [p for p in Usd.PrimRange(obj) if p.IsA(UsdGeom.Mesh)]
            old_world = original_xforms.GetLocalToWorldTransform(obj)
            old_lo, old_hi = composed_mesh_bounds(
                original_meshes, original_xforms, frame_inverse=old_world.GetInverse())
            old_poses[item.match.uuid] = (
                old_world, old_world.Transform((old_lo + old_hi) * 0.5),
            )
        else:
            preserved_before[item.match.uuid] = tuple(
                (mesh_fingerprint(p), UsdGeom.Imageable(p).ComputeVisibility(),
                 tuple(float(original_xforms.GetLocalToWorldTransform(p)[i][j])
                       for i in range(4) for j in range(4)))
                for p in Usd.PrimRange(obj) if p.IsA(UsdGeom.Mesh)
            )

    standalone_assets = tmp_path / "standalone-assets"
    shutil.copytree(BACKEND / "assets", standalone_assets)
    standalone_catalog = AssetCatalog.load(standalone_assets / "catalog.json")
    result = process_roomplan(source, BACKEND / "testdata/room.json", standalone_catalog,
                              tmp_path / "editable", metadata_path=BACKEND / "testdata/metadata.json")
    assert len([p for p in result.plan if p.model]) == 6
    assert len([p for p in result.plan if not p.model]) == 2
    assert len({p.match.uuid for p in result.plan}) == 8
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    stage = Usd.Stage.Open(str(result.root_layer))
    assert stage is not None
    assert len(result.dependencies) == 3
    assert mesh_map(stage, "/room/Mesh_grp/Arch_grp") == arch_before
    assert world_xform_map(stage, "/room/Mesh_grp/Arch_grp") == arch_xforms_before
    assert {p.match.uuid for p in result.plan if p.status == "replaced"} == {p.match.uuid for p in result.plan if p.model}
    world_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    replaced_centers = {}
    for item in result.plan:
        obj = stage.GetPrimAtPath(item.match.layer.composed_prim_paths[0])
        assert obj
        if item.model:
            original_meshes = [p for p in Usd.PrimRange(obj) if p.IsA(UsdGeom.Mesh)]
            assert original_meshes
            assert all(UsdGeom.Imageable(m).ComputeVisibility() == UsdGeom.Tokens.invisible
                       for m in original_meshes)

            replacement = replacement_for(stage, item)[1]
            assert replacement
            replacement_meshes = [p for p in Usd.PrimRange(replacement) if p.IsA(UsdGeom.Mesh)]
            assert replacement_meshes
            assert all(UsdGeom.Imageable(m).ComputeVisibility() != UsdGeom.Tokens.invisible
                       for m in replacement_meshes)
            model_prim = replacement.GetChild("Model")
            assert model_prim and model_prim.HasAuthoredReferences()
            assert all(UsdGeom.Mesh(m).GetPointsAttr().Get() for m in replacement_meshes)
            assert obj.GetCustomData().get("UUID", "").lower() == item.match.uuid
            assert obj.GetCustomData().get("Category", "").lower() == item.match.source.category

            # In the placeholder's oriented local frame, the fitted model has
            # the detected dimensions. This avoids comparing rotated world AABBs.
            replacement_world = world_cache.GetLocalToWorldTransform(replacement)
            model_lo, model_hi = composed_mesh_bounds(
                replacement_meshes, world_cache, frame_inverse=replacement_world.GetInverse())
            fitted = tuple(float(model_hi[axis] - model_lo[axis]) for axis in range(3))
            assert fitted == pytest.approx(item.match.source.dimensions, abs=TOLERANCE_METRES)

            old_world, old_center = old_poses[item.match.uuid]
            assert_matrix_pose_equal(replacement_world, old_world)
            new_center = replacement_world.Transform((model_lo + model_hi) * 0.5)
            assert tuple(float(new_center[i] - old_center[i]) for i in range(3)) == pytest.approx(
                (0, 0, 0), abs=WORLD_POSITION_TOLERANCE_METRES)
            replaced_centers[item.match.uuid] = new_center
        else:
            actual = tuple(
                (mesh_fingerprint(p), UsdGeom.Imageable(p).ComputeVisibility(),
                 tuple(float(world_cache.GetLocalToWorldTransform(p)[i][j])
                       for i in range(4) for j in range(4)))
                for p in Usd.PrimRange(obj) if p.IsA(UsdGeom.Mesh)
            )
            assert actual == preserved_before[item.match.uuid]

    # Replacements retain distinct composed poses, so replacing one chair does
    # not move another. Architecture keeps the same mesh topology and points.
    assert len({tuple(round(float(c), 5) for c in center) for center in replaced_centers.values()}) == 6
    assert len([p for p in stage.Traverse() if p.GetPath().HasPrefix("/room/Mesh_grp/Arch_grp")]) > 0
    used_layers = {Path(layer.identifier).resolve() for layer in stage.GetUsedLayers() if not layer.anonymous}
    assert set(result.dependencies).issubset(used_layers)


def make_unit_catalog(root: Path, meters_per_unit: float):
    units = {1.0: "metres", 0.01: "centimetres", 0.001: "millimetres"}[meters_per_unit]
    asset_path = root / "models" / "unit_asset.usda"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    # This cube is one physical metre wide at each authored unit scale.
    radius = 0.5 / meters_per_unit
    points = ", ".join(
        f"({x * radius}, {y * radius}, {z * radius})"
        for x, y, z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
    )
    asset_path.write_text(
        '#usda 1.0\n(\n defaultPrim = "Asset"\n metersPerUnit = '
        f'{meters_per_unit}\n upAxis = "Y"\n)\n'
        'def Xform "Asset" {\n'
        '    def Mesh "Geometry" {\n'
        f'        point3f[] points = [{points}]\n'
        '        int[] faceVertexCounts = [4, 4, 4, 4, 4, 4]\n'
        '        int[] faceVertexIndices = [0, 1, 2, 3, 4, 7, 6, 5, 0, 4, 5, 1, 1, 5, 6, 2, 2, 6, 7, 3, 4, 0, 3, 7]\n'
        '    }\n'
        '}\n', encoding="utf-8")
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    shelf = next(x for x in scan.furniture if x.category == "storage" and x.attributes.get("StorageType") == "shelf")
    models = tuple(
        CatalogModel(category, attributes, match_type, "models/unit_asset.usda", units,
                     "Y", "centered test asset", "nonuniform test fit")
        for category, attributes, match_type in (
            ("chair", {}, "category_default"), ("table", {}, "category_default"),
            ("storage", shelf.attributes, "specific"))
    )
    return AssetCatalog(root, models)


@pytest.mark.parametrize("meters_per_unit", [1.0, 0.01, 0.001], ids=["metres", "centimetres", "millimetres"])
def test_referenced_asset_units_fit_same_world_dimensions(tmp_path, meters_per_unit):
    catalog = make_unit_catalog(tmp_path / f"catalog-{meters_per_unit}", meters_per_unit)
    source = BACKEND / "testdata/room.usdz"
    result = process_roomplan(source, BACKEND / "testdata/room.json", catalog,
                              tmp_path / f"workspace-{meters_per_unit}")
    stage = Usd.Stage.Open(str(result.root_layer))
    assert stage
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    assert len([item for item in result.plan if item.model]) == 6
    for item in result.plan:
        if not item.model:
            continue
        _, replacement = replacement_for(stage, item)
        meshes = [p for p in Usd.PrimRange(replacement) if p.IsA(UsdGeom.Mesh)]
        assert meshes
        assert all(UsdGeom.Imageable(m).ComputeVisibility() != UsdGeom.Tokens.invisible for m in meshes)
        frame_inverse = UsdGeom.XformCache(Usd.TimeCode.Default()).GetLocalToWorldTransform(replacement).GetInverse()
        lo, hi = composed_mesh_bounds(meshes, UsdGeom.XformCache(Usd.TimeCode.Default()), frame_inverse=frame_inverse)
        extents = tuple(float(hi[axis] - lo[axis]) for axis in range(3))
        assert extents == pytest.approx(item.match.source.dimensions, abs=TOLERANCE_METRES)


def build_plan(scan, inventory):
    from app.usd import build_replacement_plan
    return build_replacement_plan(scan, inventory, AssetCatalog.load())
