# Adding backend-owned furniture assets

The replacement processor reads an independent catalog under backend/assets. It does not read a local Apple sample project. Keep each model and any license/attribution notice with this backend-owned copy.

## Model file and location

The current manifest validator accepts only a relative POSIX path to a checked-in .usdc file below backend/assets. USDZ is the RoomPlan input and output package format; .usd, .usda and .usdz catalog paths are not accepted by the current catalog schema. Convert and validate a new model as .usdc before registration.

Use a descriptive folder under backend/assets/models/, organized by RoomPlan category and model variant, for example:

~~~text
backend/assets/models/Chair/MyChair/MyChair.rooms.usdc
~~~

Ensure all layers and nested dependencies can be resolved. The packager copies discovered dependencies into the enhanced USDZ.

## Register the asset

Edit backend/assets/catalog.json. The top-level schema is room-twin.asset-catalog.v1 and includes catalog_version and models. Each model entry requires these fields:

- category: exact RoomPlan category string, normalized by case only during USD/category matching.
- attributes: map of exact RoomPlan attribute names and values to strings. Use an empty object for a category default.
- match_type: specific when attributes are nonempty; category_default when attributes are empty.
- path: relative POSIX path below backend/assets, ending in .usdc.
- units: metres, centimetres, millimetres or unknown. This declaration must agree with the USD stage's metersPerUnit when known.
- up_axis: Y, Z or unknown, and must agree with the stage metadata when known. The replacement engine currently requires Y-up; it does not convert axes.
- pivot: descriptive text for the model's authored origin/pivot convention.
- scaling_policy: descriptive text recording the intended fit policy. Current replacement fits model bounds to detected dimensions independently on each axis.

Specific matching uses an exact category plus exact attribute-map match. If no specific entry matches, the catalog uses an empty-attribute category_default when present. There is no partial-attribute ranking. If neither matches, the source placeholder is preserved and reported.

The pivot metadata documents asset provenance; the current engine places the fitted model bounds center at the RoomPlan furniture prim origin and preserves the furniture prim's orientation and position. Model geometry can have a nonzero authored offset from its root; fitting centers the bounds so that offset does not displace the placed replacement.

## Units, orientation and dimensions

The current scan contract uses metres and Y-up coordinates. Register the model's actual stage unit and up-axis metadata, and author useful finite, nondegenerate mesh bounds. OpenUSD references compose source coordinates verbatim, so the replacement applies a fit from the model's raw bounds to the RoomPlan dimensions converted to the destination stage units. The current policy is nonuniform per-axis fitting; do not assume proportions are preserved.

Orient the asset with Y up. The engine rejects non-Y-up geometry instead of guessing an axis conversion. Set the model's default prim and author a stable local origin. Keep pivot and scaling_policy descriptions truthful; they are catalog documentation fields and do not configure runtime behavior.

## Validate and test

From backend/ with the pinned CPython 3.12 dependencies installed:

~~~bash
python -m pip install -e ".[dev]"
python -c "from app.usd.catalog import AssetCatalog; print(len(AssetCatalog.load().models))"
python -m pytest
~~~

Catalog loading opens every .usdc with OpenUSD and validates its declared units/up axis against stage metadata. Add or update tests for new matching rules and geometry behavior. Run the real scan CLI and inspect its report when the new entry could change fixture matching:

~~~bash
python -m app.usd.cli replace --usdz testdata/room.usdz --json testdata/room.json --metadata testdata/metadata.json --output output/testscan-enhanced.usdz --force
~~~

Check replaced UUIDs, bounds, orientation, unmatched fallbacks and preserved architecture. Open the generated package in a compatible viewer when available; structural tests cannot establish rendered appearance.

## Licensing and provenance

Preserve the original copyright and license for every redistributed model. Include required notices in backend/assets next to the relevant models. The current Apple-sample-derived models retain backend/assets/LICENSE.apple.txt; keep the manifest provenance field accurate. For models from other sources, add their required notice and attribution without replacing or deleting existing notices.
