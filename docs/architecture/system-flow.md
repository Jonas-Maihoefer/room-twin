# System flow

The [system architecture](architecture.md) defines the intended MVP path:

1. The Room Twin iOS app starts an Apple RoomPlan capture.
2. RoomPlan provides structured source data.
3. A versioned API adapter maps the source data to the backend contract.
4. The app uploads the payload directly to the backend.
5. The backend validates geometry and coordinates, then selects, scales, and places replacement furniture.
6. The backend generates a GLB scene.
7. The app downloads or shares the result.

## Current implementation

The mobile foundation currently covers RoomPlan capture and local source JSON export, inspection, and sharing. It does not yet map the source into the API contract or upload it.

The backend currently exposes a health endpoint and validates a provisional versioned source envelope, returning a stub response. It does not persist or transform scan content. Furniture replacement and GLB generation are not implemented. Native RoomPlan export remains to be checked with an EAS development build on a physical compatible device. See the [Windows guide](../development/windows.md) for build and device steps.

## Responsibilities

- **iOS app:** native capture, source data handling, eventual API call, progress and error display, and result delivery.
- **Backend:** input validation, geometry and transform handling, asset selection, and GLB generation.
- **Asset library:** replacement models; a local library is sufficient for the initial pipeline.

A 3D viewer or editor may follow the MVP. It is outside the first MVP scope.
