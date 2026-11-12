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

RoomPlan dimensions are metres in Y-up coordinates. The replacement bounds are
read from the actual catalog stage with `UsdGeom.BBoxCache`; `metersPerUnit`
converts the requested target extents into authored asset units. The detected
placeholder mesh supplies the object-local position and authored orientation.
Its local point bounds are centered under a placement Xform, while a nested
model Xform applies nonuniform per-axis fitting and the corresponding pivot
translation. This preserves object placement once and avoids applying the JSON
matrix on top of the composed USD transform. `parentIdentifier` remains
semantic metadata only.

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
