from pathlib import Path

from app.usd import AssetCatalog, build_replacement_plan, load_roomplan_scan, read_usdz_inventory

BACKEND = Path(__file__).parents[1]


def test_real_scan_selects_six_models_and_preserves_two_unmatched():
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    plan = build_replacement_plan(scan, read_usdz_inventory(BACKEND / "testdata/room.usdz"), AssetCatalog.load())
    assert len(plan) == 8
    selected = [p for p in plan if p.model]
    assert len(selected) == 6
    assert sum(p.status == "preserved_no_model" for p in plan) == 2
    assert {p.model.path for p in selected} == {
        "models/Chair/Swivel_wBack_starLegs_noArms/Swivel_wBack_starLegs_noArms.rooms.usdc",
        "models/Table/Unidentified_rectangular/Unidentified_rectangular.rooms.usdc",
        "models/Storage/Shelf/shelf_vertical.rooms.usdc",
    }
    assert sum(p.model.category == "chair" for p in selected) == 3
    assert sum(p.model.category == "table" for p in selected) == 2
    assert sum(p.model.category == "storage" for p in selected) == 1
    assert {p.match.source.category for p in plan if not p.model} == {"bed", "storage"}


def test_asset_plan_deterministic():
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    catalog = AssetCatalog.load()
    inv = read_usdz_inventory(BACKEND / "testdata/room.usdz")
    assert build_replacement_plan(scan, inv, catalog) == build_replacement_plan(scan, inv, catalog)


def test_catalog_match_is_attribute_order_independent_and_unsupported_attributes_are_not_guessed():
    catalog = AssetCatalog.load()
    attributes = {
        "ChairType": "swivel", "ChairLegType": "star",
        "ChairArmType": "missing", "ChairBackType": "existing",
    }
    forward = catalog.match("chair", attributes)
    reversed_order = catalog.match("chair", dict(reversed(list(attributes.items()))))
    assert forward.status == reversed_order.status == "specific"
    assert forward.model == reversed_order.model
    unsupported = catalog.match("chair", {**attributes, "UnsupportedFeature": "yes"})
    assert unsupported.status == "category_default"
    assert unsupported.model is not None and unsupported.model.category == "chair" and not unsupported.model.attributes
    assert catalog.match("table", {"TableType": "unknown-value"}).status == "category_default"
    assert catalog.match("bed", {"Unsupported": "attribute"}).status == "missing"
