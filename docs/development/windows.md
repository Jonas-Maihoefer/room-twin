# Windows development

## Prerequisites

- Windows 11 (Windows 10 also works with supported Docker Desktop versions), PowerShell 7, Git.
- Node.js 20 LTS and npm 10+.
- Python 3.11 or newer, with the Python launcher `py` available.
- Docker Desktop using the WSL2 backend for the container workflow. Docker is optional when running Uvicorn directly.
- An Expo account, Apple Developer Program membership, and a physical RoomPlan-compatible LiDAR iPhone/iPad for native verification.

The ordinary edit/Metro loop runs on Windows. EAS compiles and signs the iOS app in the cloud; local macOS, Xcode, CocoaPods, and `expo run:ios` are not part of that loop.

## Get the repository running

From the repository root in PowerShell:

```powershell
cd apps/mobile
npm ci
Copy-Item .env.example .env
npm run start
```

The checked-in example points at `192.168.1.10`; set `EXPO_PUBLIC_API_BASE_URL` in `apps/mobile/.env` to the Windows host's actual LAN IPv4 address if you use the local backend. Expo public variables are bundled into the app and must not contain secrets.

In a second PowerShell window, run the API directly:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check `http://127.0.0.1:8000/health`. To use Docker Desktop/WSL2 instead, from the repository root run `docker compose up --build`; stop with `Ctrl+C`, or `docker compose down` in another terminal. The stub accepts a synthetic versioned envelope at `POST /scans`; it does not persist data or produce a model.

Run the backend suite in its reproducible test image with `docker compose --profile checks run --build --rm tests`.

## Build and install the iOS development client

From `apps/mobile`:

```powershell
npm install --global eas-cli
eas login
eas whoami
eas build:configure
eas build --platform ios --profile development
```

The committed `eas.json` sets an internal-distribution development client and `simulator: false`, so the target is a physical device. On the first build, EAS prompts to connect the project to an Expo account and to configure iOS credentials. Use the available Apple Developer team; allow EAS to create/manage development signing credentials, or provide credentials through EAS credentials management. Do not place certificates, private keys, provisioning profiles, or EAS tokens in the repository.

Register the test iPhone/iPad UDID with the Apple Developer team and EAS when prompted. For a new device after provisioning, register it and rebuild so the updated provisioning profile includes it. Open the EAS build link on the device and install the development build. Trust the developer profile under iOS Settings if prompted.

After installation, connect the phone and development computer to the same trusted Wi-Fi network, run `npm run start`, and open the project from the Room Twin development client. If discovery fails, run `npx expo start --dev-client --lan`; check that Windows Firewall permits Node/Expo traffic on the private LAN. `localhost` on the phone means the phone itself, not the PC. Use the PC's LAN IPv4 address for the API, or a secured tunnel for networks where direct LAN access is unavailable. Do not expose an unauthenticated API to the public internet.

## Scan verification and iteration

The native RoomPlan bridge requires the EAS development build; Expo Go does not include it. The `expo-roomplan` 1.2.1 podspec requires iOS 17 or newer. Test on a physical device with LiDAR. Grant camera access, start and finish a scan, then verify the JSON is displayed and can be shared. Record device model, iOS version, build URL, export outcome, and representative structure fields without committing room captures or personal room images. Confirm dimensions, categories, transforms, surfaces, and openings are represented in the export before defining a Room Twin conversion.

JavaScript and styles use Metro Fast Refresh. Changes to Expo config, native dependencies, config plugins, bundle settings, or iOS permissions require a new EAS development build. Windows supports the ordinary workflow; macOS/Xcode becomes useful if the wrapper needs native Swift debugging, unsupported native project changes, simulator-only diagnosis, or local iOS compilation.

## Troubleshooting

- **`npm ci` fails:** confirm Node 20 LTS, internet access to npm, and that `package-lock.json` matches `package.json`.
- **App opens but scanner is unavailable:** verify the installed app is the development build, not Expo Go; rebuild after native changes.
- **Camera denied / scan fails:** enable Camera for Room Twin in iOS Settings; confirm the device supports RoomPlan and LiDAR.
- **No `jsonUrl` or unreadable JSON:** inspect the EAS device logs and wrapper export event. The UI reports missing, unreadable, and invalid JSON separately; preserve the native JSON as evidence before designing conversion.
- **Phone cannot reach API:** use the PC's private LAN IP, confirm both devices are on the same Wi-Fi, allow the selected Python/Docker port through Windows Firewall for Private networks, and verify `/health` from the phone browser.
- **Expo cannot discover Metro:** use `--lan` and check firewall/private-network settings. A secured Expo tunnel can help on isolated networks.

## Verification record

| Stage | Evidence in this foundation |
|---|---|
| App/backend automated checks | CI definitions are committed; local results are recorded in the PR description |
| EAS cloud iOS build attempted | No — Expo account, Apple team/signing, and device registration are not available to this implementation session |
| Physical-device RoomPlan JSON inspected | No — pending a signed build and RoomPlan-compatible LiDAR device |
