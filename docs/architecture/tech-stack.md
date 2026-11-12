# Technology stack and validation status

Room Twin uses native Swift/SwiftUI on iOS, RoomPlan + ARKit for capture, and Python/FastAPI + OpenUSD (usd-core) for offline furniture replacement. USDZ is the scan input and final output.

| Layer | Technology | Current status |
| --- | --- | --- |
| iOS app | Swift, SwiftUI, Xcode; [RoomScanner](../../RoomScanner/) | Native scanner implemented; genuine scan fixture committed |
| Capture | Apple RoomPlan and ARKit | Exports USDZ, JSON and metadata on supported LiDAR hardware |
| Local preview/share | Quick Look and SwiftUI ShareLink | Implemented for local scan files |
| Transport | Swift app to FastAPI | Planned; upload and result download are not connected |
| API scaffold | Python 3.12, FastAPI, Uvicorn | GET /health; provisional JSON-only POST /scans stub, not a scan upload service |
| USD scene processing | OpenUSD Python API through usd-core==26.11 | Implemented in the offline CLI and tested against the real scan |
| Asset catalog | JSON manifest and backend-owned .usdc models | Category/attribute matching, category defaults, and missing-model preservation implemented |
| Output | Standalone USDZ plus versioned JSON report | Packaging, dependency resolution and structural/geometry checks implemented |
| CI | GitHub Actions on Ubuntu with Python 3.12 | Installs .[dev] and runs the complete backend pytest suite |

## Data and geometry

- room.usdz: RoomPlan scene and geometry references. The processor retains architectural geometry and original geometry for unsupported furniture.
- room.json: furniture UUIDs, categories, attributes, dimensions and transforms used for matching and placement.
- metadata.json: optional scan metadata; the fixture declares metres and Y-up coordinates.
- Catalog models: .usdc files registered under backend/assets/catalog.json. Entries declare category, attribute map, match type, relative path, units, up axis, pivot and scaling policy.
- Output: standalone .usdz and a sibling .report.json by default.

See the [asset authoring guide](../../backend/docs/adding-assets.md) for model and catalog constraints. This processor uses OpenUSD directly; GLB conversion is not part of the active path.

## Development environments

- The Swift scanner requires macOS/Xcode and compatible LiDAR hardware for a real capture.
- Backend development supports CPython 3.12 on Windows and Linux. usd-core==26.11 is pinned in backend/pyproject.toml.
- The GitHub Actions workflow and Docker test image use Python 3.12 on Linux.
- No React Native, Expo, Metro, EAS or browser-mock app is part of the current architecture.

See [development](../how-to-dev.md), [Windows instructions](../development/windows.md), and [validation](../testing/ios-roomplan-validation.md).
