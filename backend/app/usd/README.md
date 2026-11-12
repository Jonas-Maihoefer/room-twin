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
