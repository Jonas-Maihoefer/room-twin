# System flow — current and planned

[Chosen architecture](architecture.md) | [Technology stack](tech-stack.md)

## Current working path (offline)

~~~mermaid
flowchart LR
    A["Native Swift RoomScanner\nRoomPlan + ARKit"] --> B["Local room.usdz + room.json\n+ metadata.json"]
    B --> C["Quick Look / Share files"]
    B --> D["Approved backend/testdata fixtures"]
    D -.-> E["Future OpenUSD replacement tests"]
~~~

- The native app (`RoomScanner/`) starts and finishes scans, exports the local bundle, previews its USDZ and shares scan files.
- A real scan is checked into `backend/testdata/` and can be used on Windows or Linux to develop the backend independently of the iPhone.
- FastAPI already provides `GET /health` and a `POST /scans` JSON-validation stub. **The iOS app does not call it, and it does not process or save scans.**
- Apple's example catalog and model assets are available as input/reference material; there is **no functioning Python replacement pipeline yet**.

## Intended end-to-end workflow (not yet implemented)

~~~mermaid
flowchart TD
    IOS["Swift/SwiftUI iOS app\nRoomPlan capture"] --> RAW["USDZ + JSON + metadata"]
    RAW -. "planned authenticated upload" .-> API["FastAPI ingest / job"]
    API -.-> USD["Python + usd-core / OpenUSD"]
    MODELS["Asset catalog\nApple sample as blueprint"] -.-> USD
    USD -.-> OUTPUT["Enhanced USDZ"]
    OUTPUT -. "planned download" .-> IOS
    IOS --> VIEW["Quick Look / share USDZ"]
~~~

1. Export a RoomPlan scene and structured metadata on device.
2. **Planned:** transmit the scan bundle through FastAPI. The transport contract (such as multipart fields, job IDs and error model) must still be designed.
3. **Planned:** validate and open the USDZ, locate object meshes by their UUIDs and match the corresponding JSON categories/attributes.
4. **Planned:** select compatible assets; compute pivots and transforms, scale and place them, and preserve existing walls, floors and openings.
5. **Planned:** create a standalone enhanced USDZ with all dependencies included.
6. **Planned:** make the enhanced USDZ available to the Swift app for Quick Look and sharing.

The source USDZ is the starting geometry; the JSON provides recognition metadata. A replacement object should not cause reconstruction or destruction of the rest of the room. Unmatched objects stay as placeholders.

## Transition checklist

- [x] Native RoomPlan app exports a genuine USDZ and companion JSON.
- [x] Approved source scan fixture available in `backend/testdata/`.
- [x] FastAPI scaffold and basic tests exist.
- [ ] Python/OpenUSD asset indexing, substitution and USDZ packaging.
- [ ] Versioned file-upload / processing / result-download API.
- [ ] Swift app upload and processed-model download.
- [ ] Offline geometry tests plus full device-to-backend validation.

See [verification plan](../testing/ios-roomplan-validation.md). No GLB output step is part of the selected flow.
