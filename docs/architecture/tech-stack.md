# Technology stack

| Layer | Current foundation | Validation status |
|---|---|---|
| iOS app | TypeScript, React Native, Expo SDK 53 | Build-ready configuration; compatibility with RoomPlan bridge awaits EAS build/device test |
| iOS build | EAS internal development build | Windows-friendly cloud build; not attempted |
| Room scanning | Apple RoomPlan through `expo-roomplan` 1.2.1 | Package podspec/config plugin require iOS 17.0; JSON/USDZ export unverified on-device |
| API | Python 3.11+, FastAPI, Uvicorn | Local and Docker scaffold; versioned provisional ingestion stub |
| Future geometry/GLB | To be selected after inspecting real RoomPlan export | Out of scope here |

Package versions are pinned directly in the app manifest and backend project metadata. The JavaScript lockfile must be generated with `npm install` and committed before `npm ci`/CI is usable; registry access was unavailable in the setup environment, so do not claim this is already verified until the lockfile exists.
