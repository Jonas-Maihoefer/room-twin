# Room Twin documentation

**Decision:** native Swift/SwiftUI + RoomPlan/ARKit for scanning; Python/FastAPI + OpenUSD (`usd-core`) for planned furniture replacement; **USDZ input and output**. The app-to-backend upload is not yet implemented.

## Architecture

- [Architecture](architecture/architecture.md) — selected components, source data, ownership, and API boundaries.
- [System flow](architecture/system-flow.md) — current offline workflow versus planned FastAPI/processing path.
- [Technology stack](architecture/tech-stack.md) — chosen tools, formats, implementation status, and compatibility notes.

## Development

- [How to develop](how-to-dev.md) — Swift scanner and backend quick starts; current feature boundary.
- [Windows backend development](development/windows.md) — Python, FastAPI, tests, and offline USDZ fixture development only.

## Verification

- [RoomPlan capture and USDZ pipeline validation](testing/ios-roomplan-validation.md) — completed real-device capture and outstanding integration checks.

## Source locations

The native app lives in [`../RoomScanner/`](../RoomScanner/) (sourced from the `roomplanarkitapp` branch). The Python backend is in [`../backend/`](../backend/). Apple's [custom-models sample](../ProvidingCustomModelsForCapturedRoomsAndStructureExports/) is retained as a design reference and asset library, not as an active backend service.

The obsolete Expo/React Native `apps/` directory and its mobile build workflow have been removed. The documented FastAPI upload and enhanced USDZ download are **future work**, not features of the existing `POST /scans` stub.
