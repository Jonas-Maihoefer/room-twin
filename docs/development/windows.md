# Windows backend development

This guide covers the Python/OpenUSD backend and offline USDZ processing. The scanner is native Swift and requires macOS/Xcode; backend work uses the approved real fixture and does not require an iPhone or Mac.

## Requirements and setup

- Windows 10/11, PowerShell, Git and 64-bit CPython 3.12.
- Optional Docker Desktop for Linux-container tests.
- The backend pins [usd-core==26.11](https://pypi.org/project/usd-core/26.11/) in backend/pyproject.toml. PyPI provides CPython 3.12 wheels for Windows x86-64 and Linux x86-64.

From the repository root in PowerShell:

~~~powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
~~~

Calling the venv Python directly avoids activation and PowerShell execution-policy changes. Confirm the OpenUSD bindings:

~~~powershell
.\.venv\Scripts\python.exe -c "from pxr import Usd, UsdGeom, Sdf, UsdUtils; print('OpenUSD Python bindings OK')"
~~~

## Run the real scan

The fixture consists of backend/testdata/room.usdz, room.json and metadata.json. From backend/:

~~~powershell
.\.venv\Scripts\python.exe -m app.usd.cli replace --usdz testdata/room.usdz --json testdata/room.json --metadata testdata/metadata.json --output output/testscan-enhanced.usdz
~~~

The metadata argument is optional. By default the CLI reads assets/catalog.json. Supply --catalog path\to\catalog.json to use a different valid catalog. The output parent directory is created automatically. The report defaults to output/testscan-enhanced.report.json; --report selects a different path. Existing USDZ or report files are not overwritten unless --force is passed, which replaces the output pair. On bad inputs, invalid catalog, packaging errors or failed validation, the CLI writes an error to stderr and exits nonzero.

The expected initial fixture result is six replacements: three chairs, two tables and one shelf. The cabinet and bed stay as placeholders because the catalog has no matching model. That fallback is intentional; architecture and unmatched furniture remain in the scene.

## Tests and API

Run all backend tests from backend/:

~~~powershell
.\.venv\Scripts\python.exe -m pytest
~~~

Optional Docker test path from the repository root:

~~~powershell
docker compose --profile checks run --build --rm tests
~~~

The GitHub Actions workflow uses Ubuntu and Python 3.12, installs backend development dependencies and runs pytest. Docker's test image also copies the catalog, model assets and scan fixture.

For local API scaffold work, run:

~~~powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

GET /health is a health check. POST /scans only validates a JSON envelope and returns accepted-stub; it does not accept USDZ, save files or run replacement. Do not treat it as a working upload service.

## Validate and inspect

The generated USDZ is reopened by OpenUSD and the report records geometry/package diagnostics. To independently reopen it in a fresh process:

~~~powershell
.\.venv\Scripts\python.exe -c "from pxr import Usd, Sdf, UsdUtils; p='output/testscan-enhanced.usdz'; s=Usd.Stage.Open(p); assert s and s.GetDefaultPrim(); d=UsdUtils.ComputeAllDependencies(Sdf.AssetPath(s.GetRootLayer().identifier)); assert not d[-1], d[-1]; print('USDZ reopened; no unresolved dependencies')"
~~~

For visual inspection, open output/testscan-enhanced.usdz in a compatible USDZ viewer and compare it with testdata/room.usdz. OpenUSD structural checks do not establish rendered appearance or Apple Quick Look compatibility.

## Troubleshooting

- If py -3.12 fails, install 64-bit CPython 3.12.
- If pxr fails to import, check the venv interpreter version and architecture, then reinstall the pinned requirements.
- If the output already exists, choose another path or explicitly pass --force.
- If validation reports unresolved dependencies, check that model references and nested assets are valid USD paths.
- Do not add private room scans, camera frames or credentials to Git.

See the [architecture](../architecture/architecture.md), [development quick start](../how-to-dev.md), and [asset guide](../../backend/docs/adding-assets.md).
