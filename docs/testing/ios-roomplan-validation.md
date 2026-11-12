# RoomPlan and USDZ validation

## Implemented offline verification

The Swift scanner produces RoomPlan USDZ, JSON and metadata files. The backend can process those files independently through the Python CLI; no iOS-to-FastAPI connection is required or implemented.

From backend/, install the pinned CPython 3.12 dependencies and run:

~~~bash
python -m pip install -e ".[dev]"
python -m app.usd.cli replace \
  --usdz testdata/room.usdz \
  --json testdata/room.json \
  --metadata testdata/metadata.json \
  --output output/testscan-enhanced.usdz
python -m pytest
~~~

The test suite covers matching and fallback, transformations and model-local offsets, repeated categories, architecture preservation, package references, report contents, error handling, and real-scan integration. The CLI reopens its package and checks dependency resolution and geometry. A clean-process open check can be run with the command in the [Windows guide](../development/windows.md).

The checked-in scan contains eight furniture objects. Expected outcome with the default catalog: three chairs, two tables and one shelf are replaced; one cabinet and one bed are kept as placeholders because matching assets are unavailable. Preserving unmatched objects is intentional. Architectural geometry must remain intact.

## What automated validation establishes

OpenUSD tests and the JSON report check scene composition, UUID identity, replacement meshes, transforms, measured bounds, architecture, package-contained dependencies and missing-model fallback. The source fixture is treated as read-only; integration tests verify its content/hash remains unchanged. These checks do not render the result and do not prove perceptual quality, material appearance or Apple Quick Look compatibility.

## Manual viewer check

After generating output/testscan-enhanced.usdz, open it in Apple Quick Look/Reality Composer or another compatible USDZ viewer. Check that:

- walls, floor, doors, windows and openings remain present;
- replacements are oriented and sized plausibly and are not clipped or displaced;
- the cabinet and bed placeholders remain;
- the enhanced file opens without missing assets.

The repository's geometry diagnostic is in [furniture-placement-diagnostic.md](../../backend/docs/furniture-placement-diagnostic.md). If no compatible viewer is available, report that rendered inspection was not performed; do not infer it from structural checks.

## Planned device/API test

Swift-to-FastAPI scan upload and enhanced USDZ download are not implemented. POST /scans is only a JSON validation stub. A future end-to-end transport test must cover upload, processing orchestration, result retrieval, failure handling and preview on a supported iOS device.
