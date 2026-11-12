# Technology stack and validation status

Room Twin uses **native Swift/SwiftUI on iOS**, **RoomPlan + ARKit** for capture, and a **Python/FastAPI + OpenUSD (`usd-core`) backend** for the planned furniture-replacement workflow. **USDZ is both the source and output format.**

| Layer | Selected technology | Current status |
| --- | --- | --- |
| iOS app | Swift, SwiftUI, Xcode; [`RoomScanner/`](../../RoomScanner/) | Source present; native scanning validated by the committed real scan |
| Capture and semantic data | Apple RoomPlan | Working on supported LiDAR iPhone; room JSON and USDZ verified from device |
| AR session/camera images | ARKit, CoreImage | Native scanner uses ARKit and can save JPEG frames; frames are not required for furniture replacement |
| Local model preview / sharing | Apple's Quick Look and SwiftUI ShareLink | Present for locally exported USDZ and companion files |
| Transport | FastAPI over HTTPS (planned) | **Not connected**; file-upload/download contract not yet implemented |
| API scaffold | Python 3.11+, FastAPI, Uvicorn | `GET /health` and provisional JSON-envelope `POST /scans` returning `accepted-stub` |
| USD scene processing | [`usd-core`](https://pypi.org/project/usd-core/) / OpenUSD `pxr` Python API | **Selected, not yet implemented or declared as a backend dependency** |
| Asset catalog | RoomPlan category/attribute rules, interchangeable USD assets | Apple's sample bundle is included; Python catalog and replacement engine pending |
| Final scene | USDZ (with referenced USD layers and packaged material dependencies) | Original scan USDZ exists; enhanced USDZ generation pending |
| CI | GitHub Actions backend unit tests on Linux | Existing FastAPI tests; no native iOS build in CI |

## Data contracts and geometry

- `room.usdz`: room structure and placeholder furniture stored as a USDZ scene. Preserve the original room layout, openings and unrelated geometry.
- `room.json`: semantic labels, dimensions, transforms, object identifiers and recognition confidence; use it to inform replacements.
- `metadata.json`: device and scan metadata, including metre units and the ARKit Y-up coordinate system in the current fixture.
- `.usdc`, `.usda`: USD assets/layers used inside source and replacement scenes; correct references and packaging must be validated.
- **Output:** enhanced `.usdz`; GLB generation was dropped from the selected MVP.

The Python service will use `usd-core` to load/compose the scanned USD stage. This is **not** a Python translation of Apple's native `CapturedRoom.export()` function. Apple's [custom-models sample](../../ProvidingCustomModelsForCapturedRoomsAndStructureExports/) supplies example matching/catalog behavior and model files; the OpenUSD-based implementation and its testing remain future work.

## Development environments

- **Swift app:** requires macOS/Xcode to compile and sign; use a compatible LiDAR iPhone or iPad for real capture.
- **Backend:** Python 3.11+ on Windows or Linux; Python 3.12 is used by the current Docker image and GitHub Actions. Official `usd-core` wheels are published for Windows and manylinux, but the package has **not yet been installed into this project's dependency list**.
- **No React Native, Expo, Metro, EAS or browser-mock app** is part of the current target architecture.

See [Windows backend instructions](../development/windows.md), [general development notes](../how-to-dev.md), and [validation checklist](../testing/ios-roomplan-validation.md).
