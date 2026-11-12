"""Validated access to the backend-owned, versioned replacement asset catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class CatalogError(ValueError):
    """The catalog manifest or one of its owned USD assets is invalid."""


@dataclass(frozen=True)
class CatalogModel:
    category: str
    attributes: Mapping[str, str]
    match_type: str
    path: str
    units: str
    up_axis: str
    pivot: str
    scaling_policy: str


@dataclass(frozen=True)
class CatalogMatch:
    status: str  # "specific", "category_default", or "missing"
    model: CatalogModel | None


class AssetCatalog:
    """Load and validate the JSON manifest relative to its assets directory.

    ``match`` resolves an exact category/attribute combination first, then a
    category default. It reports missing coverage explicitly and never treats
    an Apple ``.empty`` marker as a model.
    """

    def __init__(self, root: Path, models: tuple[CatalogModel, ...]):
        self.root = root.resolve()
        self.models = models
        self._by_key = {(m.category, tuple(sorted(m.attributes.items()))): m for m in models if m.attributes}
        self._defaults = {m.category: m for m in models if not m.attributes}

    @classmethod
    def load(cls, manifest_path: str | Path | None = None, *, validate_usd: bool = True) -> "AssetCatalog":
        manifest = Path(manifest_path) if manifest_path else Path(__file__).resolve().parents[2] / "assets" / "catalog.json"
        root = manifest.parent.resolve()
        try:
            document = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CatalogError(f"cannot read catalog manifest {manifest}: {exc}") from exc
        if not isinstance(document, dict) or document.get("schema_version") != "room-twin.asset-catalog.v1":
            raise CatalogError("catalog schema_version must be 'room-twin.asset-catalog.v1'")
        if not isinstance(document.get("catalog_version"), int) or document["catalog_version"] < 1:
            raise CatalogError("catalog_version must be a positive integer")
        raw_models = document.get("models")
        if not isinstance(raw_models, list):
            raise CatalogError("catalog models must be an array")
        models: list[CatalogModel] = []
        keys: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
        for index, raw in enumerate(raw_models):
            prefix = f"models[{index}]"
            if not isinstance(raw, dict):
                raise CatalogError(f"{prefix} must be an object")
            category, attributes = raw.get("category"), raw.get("attributes")
            if not isinstance(category, str) or not category or not isinstance(attributes, dict):
                raise CatalogError(f"{prefix} requires a category and attributes object")
            if any(not isinstance(k, str) or not isinstance(v, str) for k, v in attributes.items()):
                raise CatalogError(f"{prefix}.attributes must map strings to strings")
            match_type = raw.get("match_type")
            if match_type not in {"specific", "category_default"}:
                raise CatalogError(f"{prefix}.match_type must be specific or category_default")
            if (match_type == "specific") != bool(attributes):
                raise CatalogError(f"{prefix} match_type does not agree with its attributes")
            path_value = raw.get("path")
            if not isinstance(path_value, str) or not path_value or "\\" in path_value:
                raise CatalogError(f"{prefix}.path must be a safe relative POSIX path")
            relative = Path(path_value)
            if (relative.is_absolute() or any(part in {"..", "."} for part in relative.parts)
                    or (relative.parts and ":" in relative.parts[0]) or relative.suffix.lower() != ".usdc"):
                raise CatalogError(f"{prefix}.path must be a relative .usdc file without traversal")
            resolved = (root / relative).resolve()
            if not resolved.is_relative_to(root):
                raise CatalogError(f"{prefix}.path escapes the backend asset directory")
            if not resolved.is_file():
                raise CatalogError(f"{prefix}.path does not exist: {path_value}")
            metadata = {field: raw.get(field) for field in ("units", "up_axis", "pivot", "scaling_policy")}
            if any(not isinstance(value, str) or not value.strip() for value in metadata.values()):
                raise CatalogError(f"{prefix} must specify units, up_axis, pivot, and scaling_policy")
            if raw["units"] not in {"metres", "centimetres", "millimetres", "unknown"} or raw["up_axis"] not in {"Y", "Z", "unknown"}:
                raise CatalogError(f"{prefix} has unsupported units or up_axis metadata")
            model = CatalogModel(category, dict(attributes), match_type, path_value, **metadata)
            key = (category, tuple(sorted(attributes.items())))
            if key in keys:
                raise CatalogError(f"duplicate catalog match for category {category!r} and attributes {attributes}")
            keys.add(key)
            if validate_usd:
                try:
                    from pxr import Usd, UsdGeom
                    stage = Usd.Stage.Open(str(resolved))
                except Exception as exc:  # OpenUSD reports several native exception types.
                    raise CatalogError(f"OpenUSD cannot open {path_value}: {exc}") from exc
                if stage is None:
                    raise CatalogError(f"OpenUSD cannot open {path_value}")
                actual_units = UsdGeom.GetStageMetersPerUnit(stage)
                actual_axis = UsdGeom.GetStageUpAxis(stage)
                if model.units != "unknown" and model.units != "metres":
                    expected = {"centimetres": .01, "millimetres": .001}[model.units]
                    if abs(actual_units - expected) > 1e-9:
                        raise CatalogError(f"{path_value} declares {model.units}, USD stage reports {actual_units} metres/unit")
                if model.up_axis != "unknown" and actual_axis != model.up_axis:
                    raise CatalogError(f"{path_value} declares {model.up_axis}-up, USD stage reports {actual_axis}-up")
            models.append(model)
        return cls(root, tuple(models))

    def match(self, category: str, attributes: Mapping[str, str] | None = None) -> CatalogMatch:
        """Return a specific model, a category default, or explicit missing."""
        requested = dict(attributes or {})
        model = self._by_key.get((category, tuple(sorted(requested.items()))))
        if model:
            return CatalogMatch("specific", model)
        default = self._defaults.get(category)
        if default:
            return CatalogMatch("category_default", default)
        return CatalogMatch("missing", None)
