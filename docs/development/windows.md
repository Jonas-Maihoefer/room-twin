# Windows development

Room Twin has two separate development workflows. The browser workflow needs no Apple hardware, Mac, Xcode, Apple signing, or EAS build. Use the iOS workflow only when native RoomPlan behavior is ready to validate on a LiDAR device.

## Workflow 1: Windows browser development

### Requirements

- Windows 11, PowerShell 7, Git, Node.js 22.14 or newer in the 22.x line, and npm.
- Python 3.11+ with the `py` launcher, or Docker Desktop using WSL2.

### Install and run the browser app

From the repository root:

```powershell
cd apps/mobile
npm ci
Copy-Item .env.example .env
npm run web
```

Expo opens the React Native Web app in the browser. Hot reload works for shared React Native UI. The platform-resolved web scanner is a mock: start, finish, cancel, and use **Simulate scan failure**. A finished mock scan displays and validates a RoomPlan-like JSON fixture. Its metadata says `source: room-twin-web-mock` and `authenticAppleRoomPlan: false`; it is synthetic test data, never a device capture. **Download JSON** uses a browser Blob download rather than Expo's native file system or share sheet.

The UI, status handling, and JSON inspection are shared with iOS. Platform-specific files isolate the browser mock from `expo-roomplan` and isolate native file and share APIs from web bundling.

### Start the FastAPI backend

In another PowerShell window at the repository root, use either Docker:

```powershell
docker compose up --build
```

Or run Python directly:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The commands call the virtual environment Python directly, so PowerShell activation is unnecessary. Open `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`. The example browser API URL is `http://127.0.0.1:8000`; the current API stub does not yet upload or persist the displayed scan, replace furniture, or generate GLB files. Stop services with `Ctrl+C`; use `docker compose down` if containers remain.

### Tests and debugging

From `apps/mobile`:

```powershell
npm run lint
npm run typecheck
npm test -- --ci
npx expo-doctor
npx expo install --check
npx expo config --type prebuild
npx expo export --platform web
npx expo export --platform ios
```

`expo export --platform ios` checks JavaScript bundling only; it does not compile the native iOS app. Use browser DevTools for web layout and console errors, Metro output for module resolution, and React Native Testing Library/Jest for shared workflow changes. From `backend`, run `.\.venv\Scripts\python.exe -m pytest`; or from the repository root run `docker compose --profile checks run --build --rm tests`.

This browser workflow requires no iPhone, Mac, Xcode, Expo account, Apple Developer account, or EAS compilation.

## Workflow 2: Real iOS development

### When a cloud build is needed

An EAS iOS build is needed to create the signed native development client that contains `expo-roomplan`. Expo Go cannot load this native module. You do not need a new build for ordinary TypeScript, JavaScript, styles, or web-only changes; Metro Fast Refresh updates those. Rebuild after changing native dependencies, config plugins, deployment target, bundle identifier, native permissions, or other generated iOS project settings.

Room Twin's build profile targets physical devices (`simulator: false`) and uses an internal development client distribution. EAS performs the iOS compilation remotely, so initiating the build from Windows is supported. No cloud build is part of the browser workflow.

### Bundle identifier and signing

The app uses the fixed identifier `com.jonasmaihoefer.roomtwin` in local Expo configuration and every EAS profile. This value is deterministic and does not depend on a Windows PowerShell variable being copied to EAS. It is a project setting, **not a claim that the identifier is available or registered with Apple**. Before the first EAS build, check the Apple Developer account for this exact explicit App ID. If it is unavailable, change the single value in `apps/mobile/app.config.js`, then commit and push that change before building; do not override it with a local-only environment variable. Sign into the correct Expo account and let EAS create or use the Apple development certificate and provisioning profile for the chosen team. Never commit Apple credentials, certificates, private keys, provisioning profiles, or EAS tokens.

### Scan session lifecycle

The installed `expo-roomplan@1.3.1` source keeps captured rooms, finish/export triggers, and pending export state in its native view; the JS hook has a `reset()` control, but the iOS native view exposes no reset prop. Room Twin therefore keys the adapter by each new scan ID so a restart creates a new hook and native view, captures that ID in the event callbacks, and calls the wrapper's cancel control when the scan becomes inactive. In the inspected wrapper source, successful `exportOnFinish` emits `onExported` before terminal `OK`; Room Twin accepts either callback order and reports a missing export after a timeout. This source inspection and mocked tests do not prove iOS teardown, callback delivery, or RoomPlan capture behavior. Validate cancel → restart, finish/export, and the visible overlay controls on an actual supported device when one is available.

### Register a device and install the development client

Connect a LiDAR-compatible iPhone/iPad to the Apple Developer team. From `apps/mobile`, run the EAS device registration flow and follow its browser/QR prompts:

```powershell
npx eas-cli@latest login
npx eas-cli@latest device:create
```

Then make the first compilation only after the preflight below:

```powershell
npx eas-cli@latest build --platform ios --profile development
```

On first use, EAS may ask to create/link an Expo project, select the Apple team, and configure credentials. Confirm the correct team and physical-device distribution. Install the resulting build from the EAS page on the registered device. If a device is added later, update the provisioning profile and rebuild.

To develop, start Metro from Windows:

```powershell
npm run start:dev-client -- --lan
```

Keep the device and PC on the same trusted Wi-Fi and open the project from the Room Twin development client. Allow Node/Expo traffic through Windows Firewall on the private network if asked. Use the PC's LAN IPv4 address for backend access from the phone; on the phone, `localhost` refers to the phone. A secured Expo tunnel can help when LAN discovery is unavailable.

### First-build preflight

Before consuming a quota-limited EAS compilation:

1. Connect to the intended Expo account and confirm the Apple Developer team has an active membership.
2. Confirm `com.jonasmaihoefer.roomtwin` is available as an explicit App ID under that team. If it is not, change `ios.bundleIdentifier` in `apps/mobile/app.config.js` and push that committed value before any EAS build; local environment overrides are not used.
3. Register the actual test iPhone/iPad and verify it is RoomPlan- and LiDAR-compatible.
4. From `apps/mobile`, run `npm ci`, `npx expo install --check`, `npx expo-doctor`, `npx expo config --type prebuild`, `npm run typecheck`, `npm run lint`, `npm test -- --ci`, and both `npm run export:ios` and `npm run export:web`.
5. Review the development profile in `eas.json`, select the correct Apple team when EAS prompts, and verify the profile is not set for an iOS simulator.
6. Only then run `npx eas-cli@latest build --platform ios --profile development` and install its result on the registered device.

### Validate RoomPlan on device

Grant camera permission, start a real scan, finish it through Apple's preview, inspect the exported JSON and USDZ URL, share the JSON, then repeat and cancel a scan. Check walls/surfaces, openings, object categories, dimensions, transforms, permission denial, unsupported hardware, export errors, and a second scan after cancellation. Record the device model, iOS version, build URL, and outcome. Do not commit room captures or personal room images. Browser tests validate the app workflow and mock fixture only; they cannot confirm camera permission, LiDAR availability, native capture, Apple's preview, file URLs, or iOS signing.

## Compatibility assessment

This project uses Expo SDK 57, React Native 0.86.3, and React 19.2.3, with SDK-matched Expo packages and the latest published `expo-roomplan` 1.3.1. SDK 57 is a stable supported release line; SDK 58 has since introduced the iOS 27 scene-based lifecycle, which would add native integration changes without improving this workflow. `expo-roomplan` 1.3.1 retains the documented `RoomPlanView`/`useRoomPlanView` APIs used here: controlled capture, finish/cancel, terminal status, `sendFileLoc` JSON file URLs, and export callbacks. It requires iOS 16+ and RoomPlan multi-room support requires iOS 17; Room Twin explicitly targets iOS 17. SDK 57 supports the built-in `ios.deploymentTarget` app config field, so no `expo-build-properties` plugin is needed. The native module and its Pod/Xcode/EAS compatibility remain unverified until a cloud build and a physical LiDAR-device test.

## Troubleshooting

- **`npm ci` fails:** use Node 22.14+ in the 22.x line, ensure npm access, and keep the package lock with the manifest.
- **Web fails to bundle RoomPlan:** web should resolve `ScannerSurface.web.tsx`; check imports for any direct native module reference outside the iOS adapter.
- **Native scanner unavailable:** install the Room Twin development client, not Expo Go, and rebuild after native changes.
- **Camera denied or scan fails:** enable Camera for Room Twin in iOS Settings and confirm the device supports RoomPlan and LiDAR.
- **Missing or unreadable JSON URL:** inspect the native export event and device logs. The app reports missing URLs, read failures, and invalid JSON; no hardware behavior is assumed from browser tests.
- **Phone cannot reach API:** use the PC's private LAN IP, verify both devices are on the same Wi-Fi, and allow the Python/Docker port through Windows Firewall for Private networks.
