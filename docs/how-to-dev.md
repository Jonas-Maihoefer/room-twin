# How to dev

Use this page for the short setup and day-to-day loop. The [Windows development guide](development/windows.md) has the full EAS signing, device registration, networking, and troubleshooting details.

## Setup

### Prerequisites

- Windows 11, PowerShell 7, Git, Node.js 20 LTS, and npm 10+.
- Python 3.11+ with the `py` launcher, or Docker Desktop with its WSL2 backend.
- For scanning: Expo account, Apple Developer Program membership, and a physical LiDAR iPhone/iPad running iOS 17 or newer. Expo Go cannot load RoomPlan.

### Install the app and backend dependencies

From the repository root:

```powershell
cd apps/mobile
npm ci
Copy-Item .env.example .env
```

If using the local API from the phone, edit `apps/mobile/.env` and set `EXPO_PUBLIC_API_BASE_URL` to this PC's private LAN IPv4 address, for example `http://192.168.1.42:8000`. Do not use `localhost` on the phone and do not put secrets in `EXPO_PUBLIC_` variables.

For direct Python development, open another PowerShell window at the repository root:

```powershell
cd backend
py -3 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
.\\.venv\\Scripts\\python.exe -m pip install -e ".[dev]"
```

Calling the virtual environment's Python directly avoids PowerShell's script execution policy; activation is not required.

Or use Docker Desktop from the repository root; no local Python install is needed to run the API or backend tests:

```powershell
docker compose up --build
```

### Install the iOS development build (once per device/native setup)

From `apps/mobile`, connect EAS and build a physical-device development client:

```powershell
npm install --global eas-cli
eas login
eas build:configure
eas build --platform ios --profile development
```

Follow EAS prompts to select the Apple Developer team, manage signing credentials, and register the device UDID. Install the resulting build from its EAS link on the iPhone/iPad. Detailed signing and device steps are in the [Windows guide](development/windows.md). Never commit signing credentials or EAS tokens.

## Daily routine

### Start the mobile app

In a PowerShell window:

```powershell
cd apps/mobile
npm run start
```

Open the project from the installed Room Twin development client. Keep the phone and PC on the same trusted Wi-Fi network. JavaScript and style changes update with Metro Fast Refresh.

If Metro reports that port 8081 is busy, accept an available port such as 8082; use the URL printed by Metro in the development client.

### Start the backend

Use one of these options in another PowerShell window.

With the Python environment created during setup:

```powershell
cd backend
.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or, from the repository root, use Docker Compose:

```powershell
docker compose up --build
```

Check the API from the PC with `Invoke-RestMethod http://127.0.0.1:8000/health`. From the phone, use the PC's LAN IP and allow Python/Docker through Windows Firewall on Private networks. The current `POST /scans` route only validates a provisional envelope; it does not store scans or create a GLB.

### Run checks and stop services

```powershell
# From apps/mobile
npm run lint
npm run typecheck
npm test -- --ci

# From backend
.\\.venv\\Scripts\\python.exe -m pytest

# Or run backend tests in Docker from the repository root
docker compose --profile checks run --build --rm tests
```

Stop Metro and direct Uvicorn with `Ctrl+C`. Stop the Compose stack with `Ctrl+C`, then `docker compose down` if containers remain. Changes to native dependencies, Expo config, plugins, or iOS permissions require a fresh EAS development build; regular JavaScript changes do not.
