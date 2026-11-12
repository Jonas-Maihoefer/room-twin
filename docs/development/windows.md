# Windows backend development

This guide covers **only the Python/FastAPI backend and offline USDZ processing** on Windows. Room Twin's scanner is native Swift and must be built with Xcode on a Mac; Windows is not used to compile it. **You do not need an iPhone or Mac to develop the backend against the real scan fixtures.**

## Prerequisites

- Windows 10/11, PowerShell, Git and **64-bit CPython 3.12** (the supported backend runtime).
- Optional: Docker Desktop for running backend API/tests in Linux containers.
- The backend pins [`usd-core`](https://pypi.org/project/usd-core/) and uses OpenUSD to read the checked-in USDZ and catalog models.

## First-time setup

In PowerShell from the repository root:

~~~powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
~~~

Run the tests:

~~~powershell
.\.venv\Scripts\python.exe -m pytest
~~~

Start the API with auto-reload:

~~~powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

Then open:

- Health endpoint: `http://127.0.0.1:8000/health` (returns `{"status":"ok"}`).
- OpenAPI explorer: `http://127.0.0.1:8000/docs`.

Stop the server with Ctrl+C. When calling the venv Python directly as shown, no PowerShell activation or execution-policy changes are needed.

## What the current backend actually does

- `GET /health` checks that the service is running.
- `POST /scans` accepts a provisional JSON request (`room-twin.scan-ingest.v1`, `source_format: apple-roomplan-json`), validates it, and replies `202` with `status: accepted-stub`.
- **There is no USDZ file-upload endpoint, persistence, furniture-replacement implementation or processed-USDZ download yet.** The API stub should not be used as though it accepts a scan bundle.

When the upload is implemented, the future Swift client will send a bundle including `room.usdz` and `room.json` (and metadata) to FastAPI. The backend will perform replacement with OpenUSD and return an enhanced USDZ.

## Offline USDZ development

The first real scan is already available:

~~~text
backend/testdata/
  room.usdz
  room.json
  metadata.json
~~~

Develop the processor against those fixtures. The USDZ contains separately referenced wall/floor and furniture geometry; object UUIDs can be matched to `room.json`. Preserve wall/window/door geometry and use safe fallbacks if an asset is missing. Apple's sample model catalog is in `ProvidingCustomModelsForCapturedRoomsAndStructureExports/RoomPlanExporter/RoomPlanCatalog.bundle/`.

OpenUSD is installed with the backend dependencies. The pinned `usd-core==26.11` CPython 3.12 wheel is supported on Windows x86-64; the repository CI also runs the USD integration tests on Linux. The local Issue A integration run used Python 3.14 because Python 3.12 was not installed on that workstation, so it is additional compatibility evidence rather than the supported runtime check.

~~~powershell
.\.venv\Scripts\python.exe -c "from pxr import Usd, UsdGeom, Sdf, Gf, UsdUtils; print('OpenUSD Python bindings OK')"
~~~

Use OpenUSD's supported stage/reference/packaging APIs rather than altering USDZ ZIP contents blindly. The eventual Python implementation must carefully handle asset paths, pivots, units, transforms and packaging.

## Optional Docker workflow

From the repository root, to run only the backend tests:

~~~powershell
docker compose --profile checks run --build --rm tests
~~~

To start the current backend API on port 8000:

~~~powershell
docker compose up --build api
~~~

The Docker test stage installs OpenUSD and includes the approved real scan fixture and backend assets. The API image also includes the backend-owned asset catalog; replacement and USDZ output are not implemented yet. Docker is optional for day-to-day Windows development.

## Troubleshooting and safety

- If `py -3.12` fails, install 64-bit Python 3.12.
- If the API port is occupied, stop the existing process or choose a different local port.
- If `usd-core` will not import, verify wheel availability for the Python version and architecture; prefer a 64-bit CPython build supported by PyPI.
- If the iPhone cannot eventually reach a local backend, use the PC's LAN IP rather than `localhost` from the phone. Only expose a development server on a trusted network; use HTTPS/authentication in real deployments.
- Avoid adding private room layouts, camera frames or credentials to Git. The committed scan fixture is for approved development/test use only.

See [architecture](../architecture/architecture.md) and [development quick start](../how-to-dev.md).
