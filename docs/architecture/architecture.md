# Room Twin architecture

## Components

- **Scanner:** native Swift and SwiftUI using RoomPlan for room geometry and furniture recognition and ARKit for the scan session.
- **Processor:** Python 3.12, using OpenUSD through the pinned usd-core==26.11 package. The offline processor reads scan USDZ and JSON, matches furniture, replaces supported objects and packages a standalone USDZ.
- **API scaffold:** FastAPI exposes GET /health and a provisional JSON-only POST /scans stub. The stub is not a file upload, persistence or processing service.
- **Interchange:** USDZ input and output. There is no active GLB conversion workflow.

## Implemented behavior

| Component | Current behavior |
| --- | --- |
| [RoomScanner](../../RoomScanner/) | RoomPlan capture; exports USDZ, JSON and metadata; previews/shares local files |
| Offline CLI | Opens the RoomPlan USDZ and JSON, uses metadata when supplied, replaces supported furniture, writes a USDZ and JSON report |
| Asset catalog | Backend-owned catalog maps RoomPlan category and exact attribute sets to .usdc model files; category defaults are supported |
| Fallback | Objects without a catalog match retain their original geometry and are reported as preserved |
| USDZ validation | Reopens the package, validates the default prim and dependencies, replacement/preserved mesh presence, UUID identity, transforms, bounds and architecture |
| CI | Linux GitHub Actions installs the backend extras and runs the complete pytest suite |

The checked-in real scan has eight furniture objects: three chairs, two tables, one shelf, one cabinet and one bed. The default catalog replaces the chairs, tables and shelf. The cabinet and bed are preserved because they have no matching model. All architecture remains in the scene.

## Data flow and boundaries

The iOS scanner exports room.usdz, room.json, and metadata.json. Developers currently pass these files as local CLI inputs. The parser uses RoomPlan UUIDs to correlate JSON furniture with USD prims and applies category/attribute model selection from backend/assets/catalog.json. OpenUSD edits a working copy, references backend models, and packages the result with dependencies localized inside a standalone USDZ. A versioned JSON report records each furniture decision and validation diagnostics.

The processor preserves unmatched placeholders and architectural geometry. RoomPlan dimensions use metres and Y-up coordinates in the current scan contract. Catalog models must declare units, up axis, pivot and scaling policy; the current assets are metre, Y-up .usdc models. See the [asset extension guide](../../backend/docs/adding-assets.md).

## Planned transport

Swift-to-FastAPI upload and result download are not implemented. The current POST /scans endpoint accepts only a JSON envelope and responds accepted-stub; it does not accept the USDZ/JSON bundle, store files, trigger the processor or return an enhanced scene. Authentication, persistence, jobs and the transport contract remain future work.

The scanner and offline backend work independently, so a Mac or iPhone is not required to run backend processing against the approved fixture. Building and running the Swift app does require macOS/Xcode and compatible hardware.
