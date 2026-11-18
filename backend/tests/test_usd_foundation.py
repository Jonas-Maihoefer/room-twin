from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import UUID

import pytest
from pxr import Gf, Sdf, Usd, UsdGeom, UsdUtils

from app.usd import AssetCatalog, CatalogError, ScanParseError, load_roomplan_scan, parse_roomplan_scan, read_usdz_inventory


BACKEND = Path(__file__).parents[1]
TESTDATA = BACKEND / "testdata"
ASSETS = BACKEND / "assets"


def test_openusd_imports_and_real_usdz_opens() -> None:
    assert all((Usd, UsdGeom, Sdf, Gf, UsdUtils))
    stage = Usd.Stage.Open(str(TESTDATA / "room.usdz"))
    assert stage is not None
    assert UsdGeom.GetStageUpAxis(stage) == "Y"
    assert UsdGeom.GetStageMetersPerUnit(stage) == pytest.approx(1.0)


def test_parser_loads_real_scan_and_keeps_coordinate_metadata() -> None:
    scan = load_roomplan_scan(TESTDATA / "room.json", TESTDATA / "metadata.json")
    assert len(scan.furniture) == 8
    assert {item.category for item in scan.furniture} == {"chair", "table", "bed", "storage"}
    assert [item.category for item in scan.furniture].count("chair") == 3
    assert [item.category for item in scan.furniture].count("table") == 2
    chair = next(item for item in scan.furniture if item.category == "chair")
    assert chair.attributes == {
        "ChairArmType": "missing", "ChairLegType": "star", "ChairType": "swivel", "ChairBackType": "existing"
    }
    assert isinstance(chair.identifier, UUID)
    assert len(chair.transform) == 16
    assert scan.units == "metres" and scan.up_axis == "Y"
    assert scan.reference_origin_transform is not None
    assert scan.architecture.keys() == {"walls", "doors", "windows", "openings", "floors"}


def test_parser_rejects_invalid_json_matrices_and_duplicate_identifiers() -> None:
    with pytest.raises(ScanParseError, match="cannot load"):
        load_roomplan_scan(TESTDATA / "absent.json")
    raw = json.loads((TESTDATA / "room.json").read_text(encoding="utf-8"))
    raw["objects"][0]["transform"] = [0] * 16
    with pytest.raises(ScanParseError, match="affine"):
        parse_roomplan_scan(raw)
    raw = json.loads((TESTDATA / "room.json").read_text(encoding="utf-8"))
    raw["objects"][1]["identifier"] = raw["objects"][0]["identifier"]
    with pytest.raises(ScanParseError, match="duplicate identifier"):
        parse_roomplan_scan(raw)
    raw = json.loads((TESTDATA / "room.json").read_text(encoding="utf-8"))
    raw["objects"][0]["identifier"] = "not-a-uuid"
    with pytest.raises(ScanParseError, match="valid UUID"):
        parse_roomplan_scan(raw)


def test_parser_rejects_invalid_dimensions_and_nonfinite_transforms() -> None:
    raw = json.loads((TESTDATA / "room.json").read_text(encoding="utf-8"))
    raw["objects"][0]["dimensions"] = [0, 0, 0]
    with pytest.raises(ScanParseError, match="dimensions"):
        parse_roomplan_scan(raw)
    raw = json.loads((TESTDATA / "room.json").read_text(encoding="utf-8"))
    raw["objects"][0]["transform"][0] = float("nan")
    with pytest.raises(ScanParseError, match="non-finite"):
        parse_roomplan_scan(raw)


def test_scene_inventory_finds_real_layers_uuids_and_architecture() -> None:
    inventory = read_usdz_inventory(TESTDATA / "room.usdz")
    assert len(inventory.layer_identifiers) == 17
    assert len(inventory.references) == 16
    assert len(inventory.furniture_layers) == 8
    assert len(inventory.architectural_layers) == 8
    assert inventory.up_axis == "Y"
    assert inventory.meters_per_unit == pytest.approx(1.0)
    expected_ids = {str(item.identifier).upper() for item in load_roomplan_scan(TESTDATA / "room.json").furniture}
    actual_ids = {identity.upper() for layer in inventory.furniture_layers for identity in layer.uuids}
    assert actual_ids == expected_ids
    assert sum(layer.category == "wall" for layer in inventory.architectural_layers) == 4
    assert sum(layer.category == "door" for layer in inventory.architectural_layers) == 2
    assert sum(layer.category == "window" for layer in inventory.architectural_layers) == 1
    assert sum(layer.category == "floor" for layer in inventory.architectural_layers) == 1
    assert any("Object_grp" in group for group in inventory.architectural_groups)
    assert all(layer.prim_paths and layer.source_transforms for layer in inventory.references)
    assert all(layer.composed_prim_paths and layer.composed_transforms for layer in inventory.references)


def test_catalog_loads_all_owned_models_and_selects_specific_then_default() -> None:
    catalog = AssetCatalog.load()
    assert len(catalog.models) == 56
    assert len(list((ASSETS / "models").rglob("*.usdc"))) == 56
    for model in catalog.models:
        assert (ASSETS / model.path).is_file()
        assert model.units == "metres" and model.up_axis == "Y"
    specific = catalog.match("chair", {
        "ChairType": "swivel", "ChairLegType": "star", "ChairArmType": "missing", "ChairBackType": "existing"
    })
    assert specific.status == "specific"
    assert specific.model is not None and specific.model.path.endswith("Swivel_wBack_starLegs_noArms.rooms.usdc")
    assert catalog.match("table", {"TableType": "not-present"}).status == "category_default"
    bed = catalog.match("bed")
    assert bed.status == "category_default"
    assert bed.model is not None and bed.model.path == "models/Bed/Default/DefaultBed.rooms.usdc"
    television = catalog.match("television")
    assert television.status == "category_default"
    assert television.model is not None and television.model.path == "models/Television/Default/DefaultTelevision.rooms.usdc"
    assert catalog.match("storage", {"StorageType": "cabinet"}).status == "specific"
    assert catalog.match("storage", {}).status == "category_default"


ADDED_DEFAULT_MODELS = {
    "bed": "models/Bed/Default/DefaultBed.rooms.usdc",
    "bathtub": "models/Bathtub/Default/DefaultBathtub.rooms.usdc",
    "dishwasher": "models/Dishwasher/Default/DefaultDishwasher.rooms.usdc",
    "fireplace": "models/Fireplace/Default/DefaultFireplace.rooms.usdc",
    "oven": "models/Oven/Default/DefaultOven.rooms.usdc",
    "refrigerator": "models/Refrigerator/Default/DefaultRefrigerator.rooms.usdc",
    "sink": "models/Sink/Default/DefaultSink.rooms.usdc",
    "stairs": "models/Stairs/Default/DefaultStairs.rooms.usdc",
    "stove": "models/Stove/Default/DefaultStove.rooms.usdc",
    "television": "models/Television/Default/DefaultTelevision.rooms.usdc",
    "toilet": "models/Toilet/Default/DefaultToilet.rooms.usdc",
    "washerDryer": "models/WasherDryer/Default/DefaultWasherDryer.rooms.usdc",
    "storage": "models/Storage/Default/DefaultStorage.rooms.usdc",
}


@pytest.mark.parametrize("category", sorted(ADDED_DEFAULT_MODELS))
def test_added_category_default_matches_and_is_valid_floor_pivoted_y_up_geometry(category: str) -> None:
    catalog = AssetCatalog.load()
    match = catalog.match(category)
    assert match.status == "category_default"
    _assert_model_is_valid(match, ADDED_DEFAULT_MODELS[category])


def test_cabinet_specific_match_is_valid_floor_pivoted_y_up_geometry() -> None:
    match = AssetCatalog.load().match("storage", {"StorageType": "cabinet"})
    assert match.status == "specific"
    _assert_model_is_valid(match, "models/Storage/Cabinet/Cabinet.rooms.usdc")


def _assert_model_is_valid(match, expected_path: str) -> None:
    assert match.model is not None and match.model.path == expected_path
    stage = Usd.Stage.Open(str(ASSETS / match.model.path))
    assert stage is not None
    default = stage.GetDefaultPrim()
    assert default and default.IsValid()
    assert UsdGeom.GetStageUpAxis(stage) == "Y"
    assert UsdGeom.GetStageMetersPerUnit(stage) == pytest.approx(1.0)
    # The replacement engine adds its own translate/scale to the referencing prim,
    # so the model's default prim must not carry xform ops.
    assert not UsdGeom.Xformable(default).GetOrderedXformOps()
    meshes = [prim for prim in Usd.PrimRange(default) if prim.IsA(UsdGeom.Mesh)]
    assert meshes and all(UsdGeom.Mesh(mesh).GetPointsAttr().Get() for mesh in meshes)
    box = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]).ComputeWorldBound(default).ComputeAlignedBox()
    low, high = box.GetMin(), box.GetMax()
    size = high - low
    assert all(0.3 < value < 4.0 for value in (max(size),)) and all(value > 0.1 for value in size)
    assert low[1] == pytest.approx(0.0, abs=1e-3)  # floor contact
    assert (low[0] + high[0]) / 2 == pytest.approx(0.0, abs=1e-3)
    assert (low[2] + high[2]) / 2 == pytest.approx(0.0, abs=1e-3)
    dependencies = UsdUtils.ComputeAllDependencies(Sdf.AssetPath(str(ASSETS / match.model.path)))
    assert not dependencies[-1], dependencies[-1]
    for dependency in dependencies[1]:
        assert Path(dependency).resolve().is_relative_to(ASSETS.resolve())


def test_every_model_file_on_disk_is_registered_in_the_catalog() -> None:
    catalog = AssetCatalog.load()
    registered = {model.path for model in catalog.models}
    on_disk = {path.relative_to(ASSETS).as_posix() for path in (ASSETS / "models").rglob("*.usdc")}
    assert registered == on_disk
    cabinet = catalog.match("storage", {"StorageType": "cabinet"})
    assert cabinet.status == "specific"
    assert cabinet.model is not None and cabinet.model.path == "models/Storage/Cabinet/Cabinet.rooms.usdc"
    storage_default = catalog.match("storage", {})
    assert storage_default.status == "category_default"
    assert storage_default.model is not None and storage_default.model.path == "models/Storage/Default/DefaultStorage.rooms.usdc"
    assert catalog.match("storage", {"StorageType": "shelf"}).status == "specific"


@pytest.mark.parametrize("unsafe", ["../outside.usdc", "/tmp/outside.usdc", "models\\Chair\\x.usdc", "models/placeholder.empty"])
def test_catalog_rejects_unsafe_or_nonmodel_paths(tmp_path: Path, unsafe: str) -> None:
    document = json.loads((ASSETS / "catalog.json").read_text(encoding="utf-8"))
    document["models"][0]["path"] = unsafe
    manifest = tmp_path / "catalog.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(CatalogError, match="path"):
        AssetCatalog.load(manifest, validate_usd=False)


def test_catalog_rejects_missing_files_and_bad_metadata(tmp_path: Path) -> None:
    assets_copy = tmp_path / "assets"
    shutil.copytree(ASSETS, assets_copy)
    document = json.loads((assets_copy / "catalog.json").read_text(encoding="utf-8"))
    document["models"][0]["path"] = "models/does-not-exist.usdc"
    manifest = assets_copy / "catalog.json"
    manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(CatalogError, match="does not exist"):
        AssetCatalog.load(manifest, validate_usd=False)
    document["models"][0]["path"] = "models/Chair/Default/DefaultChair.rooms.usdc"
    document["models"][0]["units"] = None
    shutil.copy2(ASSETS / "models/Chair/Default/DefaultChair.rooms.usdc", assets_copy / "models/Chair/Default/DefaultChair.rooms.usdc")
    manifest.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(CatalogError, match="units"):
        AssetCatalog.load(manifest, validate_usd=False)


def test_assets_load_from_standalone_backend_copy_without_apple_tree(tmp_path: Path) -> None:
    # Copy only backend-owned assets into an isolated tree, with no Apple sample
    # directory present or resolvable from the working directory.
    standalone = tmp_path / "service" / "assets"
    shutil.copytree(ASSETS, standalone)
    assert not (tmp_path / "ProvidingCustomModelsForCapturedRoomsAndStructureExports").exists()
    catalog = AssetCatalog.load(standalone / "catalog.json")
    assert len(catalog.models) == 56
    assert catalog.match("storage", {"StorageType": "shelf"}).status == "specific"
