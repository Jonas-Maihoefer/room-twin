# Development quick start

Room Twin has two independent parts: a native Swift scanner and an offline Python/OpenUSD processor. The processor currently receives the RoomPlan export as local CLI files. The Swift app does not upload to FastAPI or download the processed result.

## Native scanner

On macOS with Xcode and a compatible LiDAR iPhone/iPad:

1. Open RoomScanner/RoomScanner.xcodeproj in Xcode.
2. Select the RoomScanner app target, choose a signing team and compatible device, then build and run.
3. Grant camera access, perform a RoomPlan scan, and preview or share the local USDZ export.

The scanner exports room.usdz, room.json and metadata.json. It may also record JPEG frames; the replacement CLI does not use them.

## Python backend

Requires 64-bit CPython 3.12. From the repository root:

~~~bash
cd backend
python -m venv .venv
~~~

Install dependencies with the virtual environment's Python. On Windows PowerShell:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
~~~

On Linux:

~~~bash
source .venv/bin/activate
python -m pip install -e ".[dev]"
~~~

The project pins usd-core==26.11. Run the real scan through the offline CLI:

~~~bash
python -m app.usd.cli replace \
  --usdz testdata/room.usdz \
  --json testdata/room.json \
  --metadata testdata/metadata.json \
  --output output/testscan-enhanced.usdz
~~~

Metadata is optional. The default catalog is assets/catalog.json; pass --catalog path/to/catalog.json for another supported manifest. The default report is output/testscan-enhanced.report.json. Existing output pairs are protected; --force replaces both. The command returns a nonzero exit code and writes a diagnostic to stderr on invalid input or failed packaging/validation.

Run the backend suite from backend/ with python -m pytest. The tests include synthetic geometry cases and the real scan integration path. The output report contains package and geometry diagnostics. For Docker, Windows, validation and model authoring, see the [Windows backend guide](development/windows.md), [verification guide](testing/ios-roomplan-validation.md), and [asset guide](../backend/docs/adding-assets.md).

## API scaffold

The API exposes GET /health and a JSON-only POST /scans stub. That stub is not a file upload, persistence layer, replacement processor or result download service. Swift-to-FastAPI integration remains planned.

Only use scan fixtures approved for repository use. Do not commit private room layouts or camera frames.
