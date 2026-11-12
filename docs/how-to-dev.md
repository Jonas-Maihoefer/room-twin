# Development quick start

There are **two independent development environments**: a **native Swift iOS scanner** built with Xcode on a Mac, and a **Python/FastAPI backend** developed on Windows, Linux or macOS. The Python backend can use existing real scan fixtures without an iPhone.

## 1. Native scanner (Mac + compatible LiDAR device)

1. Open [`RoomScanner/RoomScanner.xcodeproj`](../RoomScanner/RoomScanner.xcodeproj) with Xcode.
2. Select the `RoomScanner` app target, choose your Apple signing team and a compatible **LiDAR-capable iPhone/iPad**, and build/run the app.
3. Grant camera access, start/finish a RoomPlan scan, preview the output using Quick Look or share the export files.
4. The current Swift `ScanManager` saves `room.usdz`, `room.json` and `metadata.json` into an on-device scan directory; it also collects optional JPEG frames while scanning.

**Status:** the app already produced the authentic example in [`backend/testdata/`](../backend/testdata/). The app **does not yet upload to FastAPI or download a processed USDZ**. iOS development and code signing require Xcode; there is no Expo/EAS workflow.

## 2. Backend (Windows, Linux or macOS)

From the repository root:

~~~bash
cd backend
python -m venv .venv
~~~

Activate the virtual environment (on Windows PowerShell, run `.\.venv\Scripts\Activate.ps1`; on macOS/Linux, run `source .venv/bin/activate`), then:

~~~bash
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

Open `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`. The current `POST /scans` validates a **JSON-only stub envelope** and returns `accepted-stub`; it is not the future upload service.

For Windows-specific commands and Docker-based test execution, see [Windows backend development](development/windows.md). The planned replacement processor will read `backend/testdata/room.usdz` together with `room.json` and use `usd-core` to create an enhanced USDZ, preserving the original room geometry. **That processor is not implemented yet.**

## 3. Working on the replacement pipeline

- Use the real [`backend/testdata/`](../backend/testdata/) bundle as the initial offline fixture.
- See the [architecture invariants](architecture/architecture.md) for UUID matching, world-space transforms, preservation of openings and safe fallback behavior.
- The [Apple sample project](../ProvidingCustomModelsForCapturedRoomsAndStructureExports/) contains reference catalog rules and starter `.usdc` models; it cannot be run as the Python backend.
- Do not claim the future FastAPI file upload or enhanced USDZ export is working until tested. Test the created USDZ with an independent 3D viewer and on iOS.
- Keep personal room scans and camera frames private; only use approved test fixtures.

## 4. Before a PR

Run the backend tests (`python -m pytest` or the Docker Compose test profile), document the changed USD geometry with regression tests once the processor exists, and have iOS changes built and verified on a compatible device. The current CI validates only the Python backend.

See [RoomPlan/end-to-end verification](testing/ios-roomplan-validation.md).
