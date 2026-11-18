# Room Twin

Room Twin combines a native Swift/SwiftUI room scanner with an offline Python/OpenUSD furniture replacement pipeline. RoomPlan and ARKit capture the room; the backend accepts the exported USDZ and JSON as local files, replaces supported furniture, and writes a standalone USDZ.

## Current workflow

1. The iOS app in [RoomScanner](RoomScanner/) scans with RoomPlan and exports `room.usdz`, `room.json`, and `metadata.json`. It can preview and share local exports with Quick Look.
2. Run the Python CLI locally with those files. It parses the RoomPlan JSON, matches furniture UUIDs to the USD scene, selects models from the independent backend catalog, applies replacements, and packages a standalone enhanced USDZ and JSON report.
3. Open the enhanced USDZ in a compatible USDZ viewer.

The Swift app does **not** upload to FastAPI or download a processed result. `POST /scans` is a JSON validation stub only; it does not receive scan files or run processing. Swift-to-FastAPI upload/download is planned. The active pipeline is USDZ-to-USDZ; GLB conversion is not used.

## What the real fixture does

The approved real scan in [backend/testdata](backend/testdata/) has eight furniture objects. With the default catalog, six are replaced (three chairs, two tables, one shelf); one cabinet and one bed remain as placeholders because no matching model is available. Preserving unsupported objects is intentional. The room architecture is preserved.

## Run the backend

Requires CPython 3.12. From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the environment in PowerShell with `.\.venv\Scripts\Activate.ps1` or on Linux/macOS with `source .venv/bin/activate`. Then install and run:

```bash
python -m pip install -e ".[dev]"
python -m app.usd.cli replace \
  --usdz testdata/room.usdz \
  --json testdata/room.json \
  --metadata testdata/metadata.json \
  --output output/testscan-enhanced.usdz
python -m pytest
```

The pinned dependencies include `usd-core==26.11`. The metadata argument is optional. The default model catalog is `assets/catalog.json`; use `--catalog path/to/catalog.json` for another supported manifest. The output directory is created as needed. The default report is `output/testscan-enhanced.report.json`. Existing USDZ or report destinations are protected; pass `--force` to replace the pair. Invalid input or failed validation prints an error to stderr and returns a nonzero exit status.

For full Windows/Linux instructions, catalog extension, diagnostics and validation details, see [docs](docs/README.md) and [backend asset guide](backend/docs/adding-assets.md).

## Repository

| Location | Purpose |
| --- | --- |
| [RoomScanner](RoomScanner/) | Native Swift/SwiftUI RoomPlan scanner |
| [backend](backend/) | FastAPI scaffold and offline Python/OpenUSD replacement processor |
| [backend/assets](backend/assets/) | Backend-owned model catalog, `.usdc` models and license notice |
| [backend/testdata](backend/testdata/) | Approved real RoomPlan USDZ, JSON and metadata fixture |
| [docs](docs/) | Architecture, development and verification documentation |

A Mac with Xcode and a supported LiDAR device is needed to build and run the scanner. Backend processing and tests can run on Windows or Linux. The automated checks validate scene structure, package dependencies and geometry; they do not prove rendered appearance or Apple Quick Look compatibility. See [manual viewer validation](docs/testing/ios-roomplan-validation.md).

Only commit scans approved for repository use. Room layouts and camera frames can be sensitive.
