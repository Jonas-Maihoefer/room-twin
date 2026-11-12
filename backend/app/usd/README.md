# Room Twin OpenUSD replacement engine

`process_roomplan(usdz_path, json_path, catalog, output_workspace, metadata_path=...)`
is the file-oriented entry point. It validates the existing RoomPlan JSON,
reads the USDZ inventory, plans by UUID, and creates an editable output
workspace. The returned `ReplacementResult` contains the copied root layer,
per-object selected model/status, and copied model dependencies. Unmatched
objects retain their source references and geometry.

## Composition and isolation

The scan root references several object layers from each shared category group.
The engine edits an isolated copy of the composed root layer and applies
visibility and replacement-reference opinions at each matched object's
composed UUID path. Editing a child below a referenced layer's default prim
would map that child at the shared reference site in this scan; root-level
overrides avoid collisions between chairs or tables. Source archive layers and
the committed test scan are not modified.

Catalog assets are copied beneath `output_workspace/scene/dependencies/` and
referenced with relative paths. The full copied scan is beneath
`output_workspace/scene/`. Keeping the root layer, original layers, and catalog
dependencies in one tree means Issue C can package `scene/` as the USDZ content
without changing replacement decisions or rewriting dependency paths.

## Transform policy

RoomPlan dimensions are metres in Y-up coordinates. Bounds are measured in the
asset's raw authored coordinates, while target dimensions are converted from
metres to destination-stage units using the destination `metersPerUnit`.
OpenUSD references compose raw coordinates and do not rescale geometry from a
referenced layer's `metersPerUnit`; fitting is therefore applied exactly once
from raw asset bounds to destination-stage units. Asset unit metadata still
describes the source asset's physical size and is validated by the catalog.

The detected placeholder mesh supplies the object-local position and authored
orientation. Since the scanned object prim is itself an `Imageable` mesh, the
replacement is authored as a sibling: only the placeholder receives the
invisible visibility opinion, and the replacement does not inherit it. The
sibling copies the placeholder's composed local placement transform once. A
nested model Xform applies nonuniform per-axis fitting and centers the model on
the placeholder's local bounds center. This avoids applying the JSON matrix on
top of the composed USD transform. `parentIdentifier` remains semantic
metadata only.

The current catalog models are metre, Y-up assets. A non-Y-up model is rejected
with a diagnostic rather than rotated speculatively. Nonuniform scale is the
default because the detected bounding dimensions are the matching target; the
standalone `fit_bounds(..., preserve_proportions=True)` helper is available for
future catalog policy. Bounds tests compare fitted model extents and the
object-local replacement center. World-axis-aligned extents can vary for
rotated or asymmetric geometry even when its placement transform is preserved.

The output is structurally inspected by OpenUSD and contains real referenced
mesh prims, but this change does not render images or establish perceptual
similarity for every asset. Mesh/material appearance and more advanced axis
conversion remain appropriate follow-up validation as the catalog grows.

## Build a standalone USDZ

Install the backend and developer dependencies from `backend/`:

```bash
python -m pip install -e ".[dev]"
```

The offline CLI reads a RoomPlan USDZ and its paired JSON export, applies the
backend-owned asset catalog, validates the result, and writes a self-contained
USDZ and a versioned JSON report:

```bash
python -m app.usd.cli replace \
  --usdz testdata/room.usdz \
  --json testdata/room.json \
  --metadata testdata/metadata.json \
  --output output/testscan-enhanced.usdz
```

`--metadata` is optional. By default, the catalog is
`backend/assets/catalog.json`; pass `--catalog assets/catalog.json` to select
another manifest. The output parent directory is created as needed. The report
defaults to `OUTPUT.report.json` next to the USDZ and has schema version
`room-twin.replacement-report.v1`; it lists deterministic per-object UUIDs,
categories, attributes, statuses, selected catalog paths, warning messages,
counts, and the final validation result. Existing output files are preserved;
use `--force` to replace both outputs.

The CLI exits with status zero only after packaging, reopening the USDZ,
checking dependency resolution, and writing the report. Invalid inputs,
catalogs, output paths, packaging failures, or failed validation return a
nonzero status and print a diagnostic to stderr. Library callers can use
`process_roomplan()` to create the editable workspace, call `package_usdz()` to
create the package, and call `validate_usdz()` independently. The library caller
owns the returned workspace lifetime; the CLI removes its temporary workspace
after packaging.

Packaging uses OpenUSD `UsdUtils.CreateNewUsdzPackage` so referenced layers,
models, and their discovered nested dependencies are localized using USDZ's
format rules. The packager writes to a temporary package, validates it, and
publishes it atomically. It does not modify the source scan or flatten the
scene. Validation opens the package as a fresh stage, requires a default prim,
checks OpenUSD dependency resolution, rejects external absolute layer paths,
and verifies the planned replacement/preserved meshes.

Run the backend suite with:

```bash
python -m pytest
```

The test suite includes the committed RoomPlan scan, architecture geometry and
transform comparisons, report checks, package dependency checks, and a fresh
process reopening the USDZ after the CLI workspace has been removed. The
`usdchecker` executable is not available in the current development environment;
the checks use the installed OpenUSD Python APIs. Apple Quick Look validation is
not performed by the automated backend suite. OpenUSD structural validity does
not establish visual appearance or Quick Look compatibility.
