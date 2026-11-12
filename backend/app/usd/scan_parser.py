"""Typed, read-only parsing for Apple's RoomPlan JSON export.

Transforms are retained as row-major 4x4 source values and are never composed
with parentIdentifier or referenceOriginTransform by this module.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID


class ScanParseError(ValueError):
    """The RoomPlan JSON is malformed or violates the supported scan contract."""


@dataclass(frozen=True)
class ScanElement:
    identifier: UUID
    category: str
    dimensions: tuple[float, float, float]
    transform: tuple[float, ...]
    parent_identifier: UUID | None = None
    confidence: str | None = None
    attributes: Mapping[str, str] | None = None


@dataclass(frozen=True)
class RoomPlanScan:
    furniture: tuple[ScanElement, ...]
    architecture: Mapping[str, tuple[ScanElement, ...]]
    units: str
    up_axis: str
    reference_origin_transform: tuple[float, ...] | None = None
    metadata: Mapping[str, Any] | None = None


_ARCHITECTURE_KEYS = ("walls", "doors", "windows", "openings", "floors")


def _uuid(value: Any, field: str, *, optional: bool = False) -> UUID | None:
    if optional and value is None:
        return None
    if not isinstance(value, str):
        raise ScanParseError(f"{field} must be a UUID string")
    try:
        return UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ScanParseError(f"{field} is not a valid UUID: {value!r}") from exc


def _matrix(value: Any, field: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != 16:
        raise ScanParseError(f"{field} must contain exactly 16 numbers")
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError) as exc:
        raise ScanParseError(f"{field} must contain only numbers") from exc
    if not all(math.isfinite(component) for component in result):
        raise ScanParseError(f"{field} contains a non-finite number")
    # Apple's flattened simd_float4x4 values are column-major. Its final row
    # occupies indices 3, 7, 11, 15 and must be the affine homogeneous row.
    if any(abs(result[index]) > 1e-5 for index in (3, 7, 11)) or abs(result[15] - 1.0) > 1e-5:
        raise ScanParseError(f"{field} is not a finite affine 4x4 transform")
    return result


def _category(value: Any, field: str) -> tuple[str, Mapping[str, str]]:
    if not isinstance(value, dict) or len(value) != 1:
        raise ScanParseError(f"{field} must be a single-key RoomPlan category dictionary")
    category, payload = next(iter(value.items()))
    if not isinstance(category, str) or not category or not isinstance(payload, dict):
        raise ScanParseError(f"{field} has an unsupported RoomPlan category encoding")
    return category, payload


def _element(value: Any, field: str, *, furniture: bool = False) -> ScanElement:
    if not isinstance(value, dict):
        raise ScanParseError(f"{field} must be an object")
    identifier = _uuid(value.get("identifier"), f"{field}.identifier")
    category, _ = _category(value.get("category"), f"{field}.category")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, list) or len(dimensions) != 3:
        raise ScanParseError(f"{field}.dimensions must contain exactly 3 numbers")
    try:
        dims = tuple(float(component) for component in dimensions)
    except (TypeError, ValueError) as exc:
        raise ScanParseError(f"{field}.dimensions must contain only numbers") from exc
    if not all(math.isfinite(component) and component >= 0 for component in dims) or not any(dims):
        raise ScanParseError(f"{field}.dimensions must be finite, non-negative, and not all zero")
    transform = _matrix(value.get("transform"), f"{field}.transform")
    parent = _uuid(value.get("parentIdentifier"), f"{field}.parentIdentifier", optional=True)
    confidence_value = value.get("confidence")
    confidence = None
    if confidence_value is not None:
        if not isinstance(confidence_value, dict) or len(confidence_value) != 1:
            raise ScanParseError(f"{field}.confidence must be a single-key dictionary")
        confidence = next(iter(confidence_value))
        if not isinstance(confidence, str) or not isinstance(confidence_value[confidence], dict):
            raise ScanParseError(f"{field}.confidence has an unsupported encoding")
    attributes: dict[str, str] | None = None
    if furniture:
        raw_attributes = value.get("attributes", {})
        if not isinstance(raw_attributes, dict):
            raise ScanParseError(f"{field}.attributes must be an object")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in raw_attributes.items()):
            raise ScanParseError(f"{field}.attributes must map string names to string values")
        attributes = dict(raw_attributes)
    return ScanElement(identifier, category, dims, transform, parent, confidence, attributes)


def parse_roomplan_scan(data: Mapping[str, Any], metadata: Mapping[str, Any] | None = None) -> RoomPlanScan:
    """Validate a decoded RoomPlan object and return furniture plus architecture."""
    if not isinstance(data, Mapping):
        raise ScanParseError("RoomPlan document must be a JSON object")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise ScanParseError("scan metadata must be a JSON object")
    objects = data.get("objects")
    if not isinstance(objects, list):
        raise ScanParseError("RoomPlan document.objects must be an array")
    furniture = tuple(_element(item, f"objects[{i}]", furniture=True) for i, item in enumerate(objects))
    architecture: dict[str, tuple[ScanElement, ...]] = {}
    identifiers: dict[UUID, str] = {}
    for key, elements in [("objects", furniture)]:
        for element in elements:
            if element.identifier in identifiers:
                raise ScanParseError(f"duplicate identifier {element.identifier} in {key} and {identifiers[element.identifier]}")
            identifiers[element.identifier] = key
    for key in _ARCHITECTURE_KEYS:
        raw = data.get(key, [])
        if not isinstance(raw, list):
            raise ScanParseError(f"RoomPlan document.{key} must be an array")
        parsed = tuple(_element(item, f"{key}[{i}]") for i, item in enumerate(raw))
        for element in parsed:
            if element.identifier in identifiers:
                raise ScanParseError(f"duplicate identifier {element.identifier} in {key} and {identifiers[element.identifier]}")
            identifiers[element.identifier] = key
        architecture[key] = parsed
    reference_transform = None
    if "referenceOriginTransform" in data:
        reference_transform = _matrix(data["referenceOriginTransform"], "referenceOriginTransform")
    units = str(metadata.get("einheit", "metres") if metadata else "metres").lower()
    if units not in {"meter", "metres", "meters", "m"}:
        raise ScanParseError(f"unsupported RoomPlan unit {units!r}; expected metres")
    up = str(metadata.get("koordinatensystem", "ARKit, y-Achse nach oben") if metadata else "Y-up")
    if "y" not in up.lower():
        raise ScanParseError(f"unsupported coordinate system {up!r}; expected Y-up")
    return RoomPlanScan(furniture, architecture, "metres", "Y", reference_transform, dict(metadata or {}))


def load_roomplan_scan(path: str | Path, metadata_path: str | Path | None = None) -> RoomPlanScan:
    """Load UTF-8 RoomPlan JSON, optionally paired with its metadata JSON."""
    try:
        source = json.loads(Path(path).read_text(encoding="utf-8"))
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8")) if metadata_path else None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScanParseError(f"cannot load RoomPlan scan: {exc}") from exc
    return parse_roomplan_scan(source, metadata)
