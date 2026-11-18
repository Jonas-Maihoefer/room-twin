from pathlib import Path
from dataclasses import replace

import pytest

from app.usd import MatchingError, load_roomplan_scan, match_furniture, read_usdz_inventory

BACKEND = Path(__file__).parents[1]


def test_real_scan_matches_all_eight_by_uuid_independent_of_order():
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    inv = read_usdz_inventory(BACKEND / "testdata/room.usdz")
    matches = match_furniture(scan, inv)
    assert len(matches) == len({m.uuid for m in matches}) == 8
    assert {m.uuid for m in matches} == {str(x.identifier) for x in scan.furniture}
    reordered = replace(scan, furniture=tuple(reversed(scan.furniture)))
    assert match_furniture(reordered, inv) == matches


def test_missing_uuid_is_explicit():
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    inv = read_usdz_inventory(BACKEND / "testdata/room.usdz")
    with pytest.raises(MatchingError, match="no USD furniture layer"):
        match_furniture(replace(scan, furniture=scan.furniture[:1]), replace(inv, furniture_layers=()))


def test_category_conflict_is_rejected():
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    inv = read_usdz_inventory(BACKEND / "testdata/room.usdz")
    layer = inv.furniture_layers[0]
    changed = replace(layer, category="not-a-category")
    with pytest.raises(MatchingError, match="category mismatch"):
        match_furniture(scan, replace(inv, furniture_layers=tuple(changed if x is layer else x for x in inv.furniture_layers)))


def test_ambiguous_duplicate_usd_uuid_is_rejected():
    scan = load_roomplan_scan(BACKEND / "testdata/room.json")
    inv = read_usdz_inventory(BACKEND / "testdata/room.usdz")
    first = inv.furniture_layers[0]
    ambiguous = replace(first, layer_identifier=first.layer_identifier + "[duplicate]")
    with pytest.raises(MatchingError, match="ambiguous USD layers"):
        match_furniture(scan, replace(inv, furniture_layers=inv.furniture_layers + (ambiguous,)))


def test_uuid_formatting_and_case_normalized():
    from app.usd import normalize_uuid
    assert normalize_uuid("{2BE035CE-5590-4D1A-A35B-0F8F1D8D3A73}") == "2be035ce-5590-4d1a-a35b-0f8f1d8d3a73"
