# How to dev

There are two development paths. Use the browser path for day-to-day frontend and backend work; it needs no Apple device or EAS build. Use the native path only to test Apple's actual RoomPlan capture.

## 1. Windows browser development

### Start the app

Requirements: Windows 11, PowerShell, Git, Node.js 22.14+ (22.x), and npm.

```powershell
cd apps/mobile
npm ci
Copy-Item .env.example .env
npm run web
```

The browser build uses the shared React Native interface and web-specific mock scanner. Start a mock scan, then finish or cancel it; **Simulate scan failure** exercises the error path. A successful export appears in the scan inspection card as validated JSON and can be downloaded. The fixture labels itself as synthetic and not Apple RoomPlan data. Browser download behavior uses the browser rather than Expo native filesystem or sharing modules.

### Start the backend

In a second PowerShell window from the repository root, use Docker Desktop/WSL2:

```powershell
docker compose up --build
```

Or use Python directly:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`. The API currently validates a provisional envelope only; it does not receive this UI's scan, persist scans, replace furniture, or produce GLB files. From a browser on the same PC, `127.0.0.1` is appropriate. For a phone later, use the PC's LAN IP.

### Check changes

From `apps/mobile`:

```powershell
npm run lint
npm run typecheck
npm test -- --ci
npx expo-doctor
npx expo install --check
npx expo config --type prebuild
npx expo export --platform ios
npx expo export --platform web
```

From the backend folder, `.\.venv\Scripts\python.exe -m pytest` runs the backend tests. Alternatively run `docker compose --profile checks run --build --rm tests` from the repository root. Use browser DevTools, Metro logs, and Fast Refresh to debug the frontend. No Apple hardware, Mac, Xcode, Apple account, Expo account, or EAS build is required for this workflow.

## 2. Real iOS development

Native RoomPlan needs an EAS-signed iOS development client because Expo Go does not include `expo-roomplan`. EAS compilation from Windows is remote. Register a real LiDAR-compatible iPhone/iPad first; confirm a free EAS compilation is worth spending before building.

The app's default identifier is `com.jonasmaihoefer.roomtwin`; availability is not verified. Confirm or register an unused explicit App ID under the correct Apple Developer team. In the build PowerShell session, set the chosen ID:

```powershell
$env:IOS_BUNDLE_IDENTIFIER = "com.your-domain.roomtwin"
```

Then authenticate, register the physical device, and initiate the development build from `apps/mobile`:

```powershell
npx eas-cli@latest login
npx eas-cli@latest device:create
npx eas-cli@latest build --platform ios --profile development
```

Follow the prompts to link the Expo project, select the Apple Developer team, and create or select signing credentials. Install the build from its EAS URL on the registered iPhone/iPad. Never commit certificates, private keys, provisioning profiles, or EAS tokens.

For daily native JS work, start Metro from Windows using `npm run start:dev-client -- --lan`. Keep the iPhone/iPad and PC on the same trusted Wi-Fi, allow Expo traffic through Windows Firewall, and open the project in the installed Room Twin development client. Use the PC's LAN IP rather than `localhost` for the API from the phone. JavaScript, TypeScript, and style changes use Fast Refresh. Native dependency, Expo plugin/config, iOS permission, deployment-target, or bundle-identifier changes need another EAS development build. See the [full Windows guide](development/windows.md) for signing, troubleshooting, compatibility notes, and the first-build preflight checklist.
