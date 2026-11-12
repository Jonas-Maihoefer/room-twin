# Room Twin — selected architecture

## Decision

- **iOS frontend:** a native **Swift + SwiftUI** project with **Apple RoomPlan** for room geometry and semantic furniture recognition, and **ARKit** for the scan session/camera frames.
- **Processing backend:** **Python + FastAPI**. **OpenUSD via `usd-core`** is the selected foundation for furniture replacement, scene composition, and self-contained USDZ output; processing is **planned, not implemented**.
- **3D interchange:** **USDZ → USDZ**. Preserve the source room geometry and replace selected placeholder objects. No GLB conversion/export is required by the MVP.
- **Backend portability:** the processing design is cross-platform (Windows/Linux), not dependent on executing the macOS/iOS RoomPlan APIs.

## Components and responsibilities

| Component | Responsibility | Today |
| --- | --- | --- |
| [`RoomScanner/`](../../RoomScanner/) | Capture using RoomPlan, export scan bundle, preview/share via Quick Look | Native scanner source present; a physical-device scan has been produced |
| Scan export | Produce `room.usdz`, `room.json`, and `metadata.json` in metres with ARKit Y-up coordinates | Implemented in `ScanManager.swift` |
| App–API transport | Authenticate and upload source files, poll/download generated USDZ and report errors | **Not implemented** |
| FastAPI | Validate/accept uploads, manage processing and result delivery | `GET /health` and provisional JSON-only `POST /scans` stub |
| OpenUSD processor | Load USDZ, match objects, compose replacement models, preserve architecture, package new USDZ | **Not implemented**; `usd-core` selected but not yet a dependency |
| Asset catalog | Choose replacement models by RoomPlan category and attributes with safe fallbacks | Apple's example catalog included; no Python matching/placement implemented |
| Result viewer | Preview/share the enhanced USDZ on the iPhone | Quick Look and sharing work for local scan files; backend result integration is planned |

## Scan bundle is the interface

The Swift scanner exports:

- **`room.usdz`** — authoritative existing 3D scene and its geometric USD references. The scanned geometry includes separate wall/floor and furniture meshes. Windows and Linux processing can use OpenUSD without re-running RoomPlan.
- **`room.json`** — Apple's structured semantic output (detected categories, subtypes/attributes, confidence, dimensions, orientation/translation transforms, UUIDs, walls, openings, windows, and floors).
- **`metadata.json`** — scan ID, iOS version, unit and coordinate-system information.
- **`frames/`** — the current Swift scanner optionally records JPEG camera frames for capture/testing; these are **not required** for the initial furniture-replacement pipeline or planned upload.

Keep the two primary sources together: do **not** assume arbitrary third-party USDZ files contain RoomPlan UUIDs or match the JSON structure. The checked-in example (`backend/testdata/`) provides the first real fixture, with four walls, one floor, two doors, one window, and eight categorized furniture objects.

## Furniture-replacement invariants

1. Open the actual USDZ as a composed USD stage with OpenUSD. Preserve walls, floor, openings, scene placement, and unaffected objects.
2. Correlate individual furniture by the UUIDs embedded in the mesh assets and in `room.json`. Do not rely on list indices or file names alone.
3. Select a model by category and available attributes (e.g., a swivel chair with a star base); support per-instance overrides later. The Apple sample's `RoomPlanCatalog.bundle/Resources` is a **starter**, not a complete catalog.
4. Resolve model pivots, axis conventions, units, dimensions, scaling and local/world transforms before replacing geometry. Verify world-space placement against the scan.
5. When a matching model is unavailable or incompatible, retain the original placeholder, report the reason, and never silently drop the object.
6. Write a **valid, self-contained USDZ** with its referenced layers, textures/materials and other dependencies localized; open it in an independent viewer.
7. Treat scan contents as untrusted input: validate file type, archive paths, limits, identifiers, size and nesting before processing.

Apple's [Providing custom models for captured rooms and structure exports](https://developer.apple.com/documentation/roomplan/providing-custom-models-for-captured-rooms-and-structure-exports) is the behavioral blueprint. Its catalog and example models live in [`ProvidingCustomModelsForCapturedRoomsAndStructureExports/`](../../ProvidingCustomModelsForCapturedRoomsAndStructureExports/). **Do not port the Swift `CapturedRoom.export(to:modelProvider:exportOptions:)` invocation literally:** the real export and model substitution are performed by Apple's native RoomPlan SDK; the Python backend must implement scene edits with OpenUSD.

## Planned FastAPI integration

The **future** API will accept at least the USDZ + JSON scan pair (plus metadata), associate them with a scan ID, and return or expose an enhanced USDZ. A multipart upload, asynchronous job state, download route, error responses, size limits, authentication and storage lifecycle still require an explicit versioned contract.

**Current reality:** `POST /scans` accepts only a provisional `room-twin.scan-ingest.v1` JSON envelope with `source_format: apple-roomplan-json` and immediately responds `accepted-stub`. It does not receive files or process the scan. Keep the working stub honest until the future API is implemented.

## MVP acceptance criteria

- Scan and export an actual room from the native Swift iOS app, preserving metadata and source USDZ/JSON.
- Upload those source artifacts through the future authenticated FastAPI connection.
- Replace at least one correctly classified object using a detailed, correctly aligned and scaled model in the Python/OpenUSD processor.
- Preserve the rest of the architectural geometry, doors and windows and any unmatched objects.
- Provide a valid enhanced USDZ that the app can retrieve and preview/share.
- Validate errors, file safety, privacy, and geometry on real-device and offline test fixtures.

A native in-app 3D editor is outside this MVP. A Mac/Xcode is required to **build the scanner**, not to **run the Python processing backend**.
