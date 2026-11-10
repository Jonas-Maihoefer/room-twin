# Technology stack

The system architecture is chosen: a custom iOS app using Apple RoomPlan, direct backend integration, furniture replacement, and GLB output. The technologies below establish the first foundation; native compatibility and the complete processing path still need validation.

## Chosen requirements

| Area | Requirement |
|---|---|
| Client | Custom iOS app with integrated scan |
| Capture | Apple RoomPlan on a supported LiDAR device |
| Transfer | Direct API upload using structured room and object data |
| Processing | Backend geometry and asset pipeline |
| MVP output | GLB available to download and share in the app |
| Later work | In-app viewer or editor only after the MVP |

## Current implementation and validation

| Area | Current foundation | Validation status |
|---|---|---|
| iOS app | TypeScript, React Native, Expo SDK 53 | App checks are recorded in the PR description; device build and native compatibility remain pending |
| iOS build | EAS internal development build | Cloud build not attempted; Expo project access, Apple signing, and device registration are required |
| Room scanning | Apple RoomPlan through expo-roomplan 1.2.1 | Wrapper podspec and config plugin require iOS 17; JSON and USDZ export have not been verified on-device |
| API | Python 3.11+, FastAPI, Uvicorn | Local and Docker scaffold with a provisional versioned ingestion stub |
| Geometry and GLB | To be selected after inspecting real RoomPlan exports | Not implemented |

The JavaScript package versions are recorded in the app manifest and lockfile. The RoomPlan wrapper is isolated behind an app-facing adapter so its version-specific surface can be changed independently.

## Data formats

- **Capture:** Apple's structured RoomPlan result, with its actual exported fields to be confirmed on-device.
- **API input:** a future explicit, versioned mapping that preserves or deliberately handles dimensions, categories, transforms, surfaces, and openings. The provisional envelope treats the source JSON as opaque.
- **MVP output:** GLB as a portable 3D scene.
- **Additional formats:** only if separately required; formats such as BLEND could need extra processing.

Expo Go cannot load the native RoomPlan module. A signed EAS development build and a physical compatible LiDAR device are required to validate capture and export. See the [RoomPlan validation plan](../testing/ios-roomplan-validation.md).
