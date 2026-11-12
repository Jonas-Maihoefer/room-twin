# Room Twin documentation

The current implementation is a native Swift/SwiftUI RoomPlan + ARKit scanner and an offline Python/OpenUSD furniture replacement processor. RoomPlan scan files are currently supplied to the processor as local CLI inputs. Swift-to-FastAPI upload/download is planned and is not implemented.

## Architecture

- [Architecture](architecture/architecture.md) — components, ownership, data and API boundaries.
- [System flow](architecture/system-flow.md) — implemented offline path and planned transport.
- [Technology stack](architecture/tech-stack.md) — versions, formats and status.

## Development

- [Development quick start](how-to-dev.md) — iOS and backend setup.
- [Windows backend guide](development/windows.md) — Windows setup, CLI, tests and Docker.
- [Adding backend assets](../backend/docs/adding-assets.md) — catalog schema, model constraints, validation and licensing.
- [Backend USD processor](../backend/app/usd/README.md) — processing and packaging details.

## Verification

- [RoomPlan and USDZ validation](testing/ios-roomplan-validation.md) — automated checks and manual viewer limits.
- [Furniture placement diagnostic](../backend/docs/furniture-placement-diagnostic.md) — geometry measurements and placement regression context.

The native app is in [RoomScanner](../RoomScanner/). The Python backend and its independent catalog are in [backend](../backend/). The obsolete Apple sample project is not part of this repository.
