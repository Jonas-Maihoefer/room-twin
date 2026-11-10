# Chosen system architecture

Room Twin's MVP uses a custom iOS app with Apple RoomPlan and a directly connected backend.

## Intended MVP flow

1. A user scans a room inside the Room Twin app on a supported LiDAR iPhone or iPad.
2. The app receives structured RoomPlan data about surfaces, openings, and recognized objects.
3. A versioned adapter prepares a payload that matches the backend contract. RoomPlan does not define Room Twin's API schema.
4. The app sends the payload directly to the backend.
5. The backend validates the input and coordinate systems, processes room geometry, and places suitable 3D assets.
6. The backend makes a GLB available for the app to download and share.

## Responsibilities

| Component | Responsibility |
|---|---|
| iOS app | Start and finish scans, show progress and errors, prepare and upload data, retrieve and share results |
| RoomPlan integration | Capture rooms with LiDAR and provide Apple's structured room and object data |
| API adapter | Map source data into a versioned backend payload while preserving dimensions, categories, transforms, surfaces, and openings |
| Backend API | Validate uploads, start or perform processing, handle errors, and provide results |
| Geometry and asset pipeline | Interpret room geometry, select replacement assets, scale and place them, and build a scene |
| Asset library | Provide suitable 3D models for recognized object categories |
| Model export | Produce a usable GLB file |

## Current implementation boundary

The app foundation in this repository exercises RoomPlan capture, reads the exported source JSON, and displays and shares that file. Its wrapper is isolated behind an adapter. The backend provides a health endpoint and a provisional versioned scan-ingestion envelope; it validates the envelope and returns a stub response without storing or transforming scan content.

The source export and backend payload are separate formats. The actual RoomPlan fields and export behavior must be inspected on-device before defining a mapping. The provisional source payload is opaque and does not assign Room Twin meaning to Apple's fields. This foundation does not implement API upload from the app, furniture matching, geometry processing, GLB generation, or production storage.

The Expo RoomPlan wrapper is a candidate integration. Expo Go does not include this native module. The app targets iOS 17 based on the wrapper's podspec and config plugin, but only a successful EAS build and physical-device JSON inspection can validate the path.

## MVP scope and constraints

The first MVP demonstrates scan in the app, structured data transfer, direct backend upload, at least one correctly scaled and positioned replacement asset, GLB generation, and download or sharing in the app. A 3D viewer or editor is a later extension, not a requirement for this MVP.

The API schema, error model, upload limits, authentication, temporary storage, and result retrieval behavior remain to be designed. Indoor scans can contain sensitive information; use secured transfer and do not commit private room captures.
