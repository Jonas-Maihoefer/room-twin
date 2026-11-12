# System flow — implemented and planned

[Architecture](architecture.md) | [Technology stack](tech-stack.md)

## Implemented local scan-to-USDZ workflow

~~~mermaid
flowchart LR
    A["Swift/SwiftUI iOS scanner<br/>RoomPlan + ARKit"] --> B["room.usdz + room.json<br/>+ metadata.json"]
    B --> C["Local Python CLI<br/>OpenUSD / usd-core"]
    M["Backend-owned catalog<br/>catalog.json + .usdc models"] --> C
    C --> D["Standalone enhanced USDZ<br/>+ replacement report"]
    D --> E["Compatible USDZ viewer"]
~~~

1. The native Swift scanner captures a room with RoomPlan and exports USDZ and JSON scan data plus metadata.
2. A developer supplies those files to the Python CLI as local inputs; the iOS app does not call the backend.
3. The backend parses the JSON, inspects the USD scene, matches furniture by UUID, and selects a backend-owned model using category and attribute rules.
4. OpenUSD replaces supported furniture while preserving unmatched placeholders and room architecture.
5. OpenUSD packages a standalone enhanced USDZ. A JSON report records per-object decisions and package/geometry diagnostics.
6. The enhanced USDZ can be opened independently in a compatible viewer. The processor does not render or prove visual quality.

The real fixture initially contains eight furniture objects: three chairs, two tables and one shelf are replaced; one cabinet and one bed are preserved because the catalog has no matching model. This is intentional fallback behavior.

## Planned iOS/API transport

~~~mermaid
flowchart LR
    IOS["Swift app"] -. "planned upload" .-> API["FastAPI transport"]
    API -. "planned local processing orchestration" .-> CLI["Python/OpenUSD processor"]
    CLI -. "planned result download" .-> IOS
~~~

Swift-to-FastAPI upload and enhanced USDZ download are not implemented. The existing POST /scans accepts only a JSON validation envelope and responds accepted-stub; it does not accept USDZ files, persist scans or invoke processing. Authentication, storage, jobs and a transport contract remain future work.

## Status

- [x] Native RoomPlan app exports real USDZ, JSON and metadata.
- [x] Offline Python/OpenUSD replacement CLI and independent backend asset catalog.
- [x] Standalone USDZ packaging and automated package/geometry validation.
- [x] Real scan fixture and backend integration tests.
- [ ] Swift upload and processed USDZ download through FastAPI.
- [ ] Manual rendered viewer verification on the generated result.

See the [verification guide](../testing/ios-roomplan-validation.md). No GLB output step is part of the selected architecture.
