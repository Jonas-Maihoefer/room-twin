# Documentation

**Architecture status: chosen.** Room Twin uses a custom iOS app with Apple RoomPlan and direct backend integration. Open implementation details do not change that architecture decision.

## Architecture

1. [System architecture](architecture/architecture.md) — components, responsibilities, MVP scope, and integration boundaries.
2. [System flow](architecture/system-flow.md) — the intended path from room scan to model delivery, with the current implementation boundary.
3. [Technology stack](architecture/tech-stack.md) — chosen requirements, implementation technologies, and validation status.

## Development

- [How to dev](how-to-dev.md) — setup and daily development routine.
- [Windows development](development/windows.md) — EAS signing, device registration, networking, and troubleshooting.

## Verification

- [iOS RoomPlan and end-to-end validation](testing/ios-roomplan-validation.md) — plan for proving the real scan-to-model pipeline on a supported device.

## Current implementation

The repository contains an Expo app foundation and a FastAPI scaffold. The app can exercise the native capture/export path, but physical-device validation remains pending. The backend ingestion route is a provisional stub; the complete upload, furniture replacement, and GLB pipeline are not implemented.
