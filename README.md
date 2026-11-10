# Room Twin

Room Twin's MVP path is a custom iOS app using Apple RoomPlan, structured scan data sent directly to a backend API, furniture replacement, and a downloadable/shareable GLB. The repository is the first executable foundation for that path.

## Repository layout

- `apps/mobile/` — TypeScript Expo app and isolated RoomPlan adapter.
- `backend/` — FastAPI health endpoint and versioned scan-ingestion seam.
- `docs/architecture/` — chosen system flow, technology choices, and payload boundary.
- `docs/development/windows.md` — Windows setup, EAS signing, device workflow, and troubleshooting.

## Quick start

See [Windows development setup](docs/development/windows.md) for prerequisites and exact PowerShell commands. In brief, install Node.js 20 LTS, Python 3.11+, and Docker Desktop with WSL2; then run `npm ci` and `npm run start` in `apps/mobile`, and `python -m venv .venv` followed by the backend setup commands from `backend/`.

The RoomPlan module is native and does not run in Expo Go. Start with a signed EAS development build and a physical LiDAR-capable iPhone/iPad. Ordinary JavaScript edits use Fast Refresh; native dependency/config changes require a new development build.

## Verification status

| Check | Status |
|---|---|
| Source, app configuration, docs, and backend scaffold | Implemented in this foundation |
| Local npm / Python checks | Pending in this environment (see PR check results) |
| GitHub Actions | Runs app lint/typecheck/tests and backend pytest on pull requests |
| EAS cloud iOS development build | Not attempted; requires Expo access and Apple signing/team setup |
| On-device RoomPlan JSON export | Pending physical LiDAR device verification |
| Scan-to-furniture-to-GLB product flow | Out of scope for this foundation |

RoomPlan JSON is Apple-generated source data. The versioned Room Twin API contract is separate and provisional; no conversion that could discard source semantics is implemented here.
