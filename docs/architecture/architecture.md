# Chosen system architecture

Room Twin's MVP path is the integrated custom iOS application:

```mermaid
flowchart LR
  A[Expo React Native iOS app] --> B[Apple RoomPlan scan]
  B --> C[Apple structured JSON export]
  C --> D[Explicit versioned API adapter]
  D --> E[FastAPI backend]
  E --> F[Furniture replacement]
  F --> G[GLB download and share]
```

The implementation begins by proving the native RoomPlan export path. The app runs a RoomPlan capture through an isolated wrapper adapter, receives the exported JSON file URL, reads and displays the source file, and makes it shareable. No scan conversion or backend upload is implied by this first vertical slice.

The backend exposes health plus a deliberately provisional `room-twin.scan-ingest.v1` contract stub. It validates the envelope and returns `accepted-stub`; it does not persist or transform scan content. Asset matching, furniture replacement, scene generation, GLB export, user accounts, and production storage remain later work.

## Source data versus API data

Apple RoomPlan JSON is a native source format whose concrete fields and export behavior must be inspected on-device. `source_payload` in the provisional v1 envelope is an opaque JSON object intended to preserve that source verbatim. It does not assign Room Twin meaning to Apple's fields. A future adapter must version its mapping and demonstrate that dimensions, categories, transforms, surfaces, and openings are retained or explicitly handled before ingestion semantics are finalized.

The `expo-roomplan` package is a candidate bridge, not a validated product dependency. Its README describes RoomPlan on iOS 16+, but version 1.2.1's actual podspec and config plugin require iOS 17.0; the project therefore targets iOS 17. Upstream documents a `RoomPlanView` export callback with `sendFileLoc` and `jsonUrl`; published Expo/React Native peer dependencies are wildcards and the package's development environment is Expo 53 / React Native 0.79.1. That does not establish compatibility with every Expo SDK. This repository pins an Expo 53 combination for an initial cloud/device trial; only a successful EAS build and physical-device JSON inspection can validate the path.
