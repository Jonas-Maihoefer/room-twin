"""Deterministic UUID matching and catalog planning for RoomPlan objects."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.usd.catalog import AssetCatalog, CatalogModel
from app.usd.scan_parser import RoomPlanScan, ScanElement
from app.usd.scene_reader import SceneInventory, SourceLayer


class MatchingError(ValueError):
    """The scan and USD inventory have conflicting or ambiguous identities."""


def normalize_uuid(value: str | UUID) -> str:
    try:
        return str(value if isinstance(value, UUID) else UUID(str(value).strip().strip("{}"))).lower()
    except (ValueError, AttributeError, TypeError) as exc:
        raise MatchingError(f"invalid UUID {value!r}") from exc


@dataclass(frozen=True)
class FurnitureMatch:
    source: ScanElement
    layer: SourceLayer
    uuid: str
    parent_identifier: UUID | None


@dataclass(frozen=True)
class ReplacementPlanItem:
    match: FurnitureMatch
    model: CatalogModel | None
    match_type: str
    status: str


def match_furniture(scan: RoomPlanScan, inventory: SceneInventory) -> tuple[FurnitureMatch, ...]:
    layers: dict[str, list[SourceLayer]] = {}
    for layer in inventory.furniture_layers:
        for identity in layer.uuids:
            layers.setdefault(normalize_uuid(identity), []).append(layer)
    result = []
    seen: set[str] = set()
    for obj in scan.furniture:
        identity = normalize_uuid(obj.identifier)
        if identity in seen:
            raise MatchingError(f"duplicate furniture UUID in scan: {identity}")
        seen.add(identity)
        candidates = layers.get(identity, [])
        if not candidates:
            raise MatchingError(f"no USD furniture layer for UUID {identity}")
        unique = {candidate.layer_identifier: candidate for candidate in candidates}
        if len(unique) != 1:
            raise MatchingError(f"ambiguous USD layers for UUID {identity}: {sorted(unique)}")
        layer = next(iter(unique.values()))
        if layer.category.lower() != obj.category.lower():
            raise MatchingError(f"category mismatch for {identity}: scan={obj.category}, USD={layer.category}")
        result.append(FurnitureMatch(obj, layer, identity, obj.parent_identifier))
    return tuple(sorted(result, key=lambda item: item.uuid))


def build_replacement_plan(scan: RoomPlanScan, inventory: SceneInventory, catalog: AssetCatalog) -> tuple[ReplacementPlanItem, ...]:
    plan = []
    for match in match_furniture(scan, inventory):
        selected = catalog.match(match.source.category, match.source.attributes)
        plan.append(ReplacementPlanItem(match, selected.model, selected.status,
                                        "planned" if selected.model else "preserved_no_model"))
    return tuple(plan)
