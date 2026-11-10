# Room Twin

Room Twin turns indoor LiDAR scans into reusable 3D room models. Its chosen MVP uses a custom iOS app with Apple RoomPlan, a backend pipeline for furniture replacement, and GLB download and sharing.

## Chosen architecture

The scan runs inside the Room Twin app on a supported LiDAR iPhone or iPad. The app will send structured scan data directly to a backend API. The backend will replace selected furniture with positioned 3D assets and return a GLB file. An in-app viewer or editor is outside the first MVP.

## Current implementation status

This pull request establishes the Expo iOS app foundation, a RoomPlan capture and source JSON inspection path, and a FastAPI health endpoint with a provisional scan-ingestion stub. The native RoomPlan export still needs validation in an EAS development build on a physical device. Scan conversion, upload, furniture replacement, and GLB generation are not implemented yet.

## Documentation

- [System architecture](docs/architecture/architecture.md)
- [System flow and implementation boundary](docs/architecture/system-flow.md)
- [Technology stack and validation](docs/architecture/tech-stack.md)
- [How to dev: setup and daily routine](docs/how-to-dev.md)
- [Windows setup, EAS signing, and device verification](docs/development/windows.md)
- [RoomPlan and end-to-end validation plan](docs/testing/ios-roomplan-validation.md)
- [Documentation index](docs/README.md)
