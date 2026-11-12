# Room Twin

Room Twin turns LiDAR room scans into editable, reusable 3D room scenes. The selected architecture is **a native Swift/SwiftUI iOS scanner (RoomPlan + ARKit)** and **a Python/FastAPI backend using OpenUSD (`usd-core`)** to replace RoomPlan furniture placeholders with detailed assets. **USDZ is the scan input and final 3D output.** A GLB export pipeline is no longer part of the MVP.

## Architecture

1. The native iOS app in [`RoomScanner/`](RoomScanner/) scans a room with Apple RoomPlan and exports `room.usdz`, `room.json`, and `metadata.json`. It can preview the USDZ with Quick Look and share the exported files.
2. **Planned:** the app uploads the scan bundle to FastAPI. The upload and result-download connection **are not implemented** yet.
3. **Planned:** the Python backend uses [`usd-core`](https://pypi.org/project/usd-core/) (OpenUSD's `pxr` bindings) to open the source USDZ, match individual furniture by category/attributes/UUID from the JSON, and substitute correctly transformed 3D models without rebuilding the room walls and openings.
4. **Planned:** the backend packages an enhanced USDZ for the app to download, preview, or share.

Apple's [custom-models RoomPlan sample](ProvidingCustomModelsForCapturedRoomsAndStructureExports/) is a **reference implementation and starter model catalog**, not an executable Python backend or a dependency on macOS at runtime. The Python implementation must reproduce the desired behavior with OpenUSD; it cannot directly call Apple's `CapturedRoom.export(modelProvider:)` API.

## What works today

- **Real device scan verified:** the Swift scanner generated a genuine RoomPlan scan; a curated example is in [`backend/testdata/`](backend/testdata/) (`room.usdz`, `room.json`, `metadata.json`). The Swift source was brought from the [`roomplanarkitapp` branch](https://github.com/Jonas-Maihoefer/room-twin/tree/roomplanarkitapp).
- **Backend scaffold:** `GET /health` and `POST /scans` exist. `POST /scans` only validates a provisional JSON envelope and returns `accepted-stub`; it **does not accept USDZ uploads, store scans, perform replacement, or return a processed model**.
- **Future work:** select and scale replacement assets, implement reliable USD composition and USDZ packaging, design the upload/result API, then validate an end-to-end scan on a device. The `usd-core` dependency is selected but **not yet installed or used** by the backend.

## Repository

| Location | Purpose |
| --- | --- |
| [`RoomScanner/`](RoomScanner/) | Native Xcode/SwiftUI scanner, on-device USDZ/JSON export and Quick Look |
| [`backend/`](backend/) | Python 3.11+ / FastAPI foundation; planned `usd-core` asset replacement |
| [`backend/testdata/`](backend/testdata/) | Approved real-world RoomPlan input fixtures for offline backend development |
| [`ProvidingCustomModelsForCapturedRoomsAndStructureExports/`](ProvidingCustomModelsForCapturedRoomsAndStructureExports/) | Apple's example, license, catalog and sample `.usdc` assets |
| [`docs/`](docs/) | Architecture, development and verification |

A Mac with Xcode and a compatible LiDAR iPhone/iPad is needed to compile and run the scanner. **Backend development and USD scene processing can be done on Windows/Linux without a Mac.** See the [development guide](docs/how-to-dev.md) and [Windows backend guide](docs/development/windows.md).

## Documentation

- [Architecture and responsibility boundaries](docs/architecture/architecture.md)
- [Current and planned system flow](docs/architecture/system-flow.md)
- [Technology stack and implementation status](docs/architecture/tech-stack.md)
- [Developer quick start](docs/how-to-dev.md)
- [Windows backend development](docs/development/windows.md)
- [Device and end-to-end validation](docs/testing/ios-roomplan-validation.md)
- [Documentation index](docs/README.md)

Indoor layouts can be sensitive. Only commit scans explicitly approved for repository use; do not commit private captures or camera frames.
