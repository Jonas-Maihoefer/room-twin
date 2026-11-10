# Room Twin: macOS + iPhone development

This guide is for a developer using **a Mac and a physical, LiDAR-capable iPhone** to build and test Room Twin locally. It covers the first-time setup, the first native build, the Python backend, everyday development, testing, and troubleshooting.

**Recommended approach:** build the development app locally using Xcode, then use Metro/Fast Refresh for normal JavaScript and TypeScript changes. **EAS cloud builds are not needed for this workflow.** The browser mock remains optional; it is not a prerequisite for iOS development.

> **Current project status (November 2026):** The repository contains an Expo/React Native iOS app with `expo-roomplan` and an isolated RoomPlan adapter, plus a FastAPI backend. Real iPhone capture/export has **not yet been validated**. The UI can inspect and share scan JSON, but it does not yet upload it to the API. The API currently accepts a provisional envelope at `POST /scans` without storing or processing it. Furniture replacement and GLB generation are not implemented.

## 1. Prerequisites

### Hardware and accounts

- A Mac able to run an Xcode version compatible with the project's Expo SDK.
- An iPhone or iPad **with LiDAR and RoomPlan support**, running **iOS/iPadOS 17 or newer** (the app's configured minimum). A normal iPhone without LiDAR cannot validate scans.
- A compatible USB cable for initial pairing (wireless debugging is optional later).
- An Apple Account added to Xcode for local code signing.
- GitHub access to the [`Jonas-Maihoefer/room-twin`](https://github.com/Jonas-Maihoefer/room-twin) repository.
- A trusted local network shared by the Mac and iPhone for Metro and, eventually, local API requests.

A **paid Apple Developer Program membership is not required** to build and test on your own device using Xcode's free *Personal Team*. Free provisioning profiles expire after **7 days**; rebuild/reinstall as necessary. Paid team membership is useful for broader distribution and other Apple capabilities. No Expo account or EAS device registration is necessary for local builds.

### Versions used by this repository

Check `apps/mobile/package.json` and `backend/pyproject.toml` before making upgrades:

| Component | Version / requirement |
| --- | --- |
| Node.js | **22.14+**, staying on Node **22.x** |
| npm | Bundled with Node.js |
| Python | **3.11+** (examples below use 3.12) |
| Expo | SDK **57** |
| React Native | **0.86.3** |
| `expo-roomplan` | **1.3.1** |
| iOS deployment target | **17.0** |
| Xcode | Install a compatible full Xcode release; [Expo's SDK reference](https://docs.expo.dev/versions/latest/) lists the current minimum for SDK 57 (at the time of writing, **Xcode 26.4+**) |

Do **not** upgrade Expo or `expo-roomplan` just to follow this guide: a native compatibility check on a real device is the next milestone.

## 2. One-time Mac setup

### 2.1 Install and prepare Xcode

1. Install **Xcode** from the Mac App Store (use a version compatible with your macOS and the Expo SDK).
2. Open Xcode once. Accept its license and install any requested components.
3. In **Xcode > Settings > Locations**, choose the installed Xcode version under **Command Line Tools**.
4. Install the iOS platform support in **Xcode > Settings > Components** if prompted.
5. Open Terminal and verify:

   ```bash
   xcode-select -p
   xcodebuild -version
   xcrun --version
   ```

   If the selected developer directory is wrong, use:

   ```bash
   sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
   ```

   If Xcode asks for additional setup, finish it in Xcode before proceeding. Do not point `xcode-select` only at `/Library/Developer/CommandLineTools` when building an iOS app.

### 2.2 Install Git, Node.js, Python, and CocoaPods

The commands below use [Homebrew](https://brew.sh/). Install Homebrew from its official site if it is not already available, and follow its instructions to add `brew` to your shell's PATH.

```bash
brew update
brew install git node@22 python@3.12 cocoapods
```

Homebrew may install `node@22` without making it the default Node version. To put it first in your default **zsh** shell's PATH:

```bash
echo 'export PATH="$(brew --prefix node@22)/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile
```

Verify the tools:

```bash
git --version
node --version
npm --version
python3.12 --version
pod --version
```

`node --version` should report **v22.14.0 or newer within v22.x**. If you already manage Node via a version manager, you can use that instead of the Homebrew PATH change. Avoid conflicting Node installations.

An editor such as VS Code is optional; use whichever editor or coding agent you prefer.

### 2.3 Clone the repository

Choose a directory for your projects and clone Room Twin:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/Jonas-Maihoefer/room-twin.git
cd room-twin
```

If you normally use SSH with GitHub, the SSH clone URL works just as well.

### 2.4 Install the mobile dependencies

```bash
cd ~/Projects/room-twin/apps/mobile
npm ci
cp .env.example .env
```

The copied `.env` initially points to the Mac loopback address. Section 5 explains how to change it to the Mac's LAN IP before using the backend from the iPhone.

Use `npm ci` for a clean install matching `package-lock.json`. Do not run `npm install` simply to install the already-locked dependencies.

Check the Expo configuration and dependencies:

```bash
npx expo install --check
npx expo-doctor
npx expo config --type prebuild
```

Address any *actual* errors before the first native build. The app already declares `expo-dev-client` and `expo-roomplan` and registers their plugins in `app.json`.

### 2.5 Set up the Python backend

Open a separate Terminal window:

```bash
cd ~/Projects/room-twin/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Start the development API:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify on the Mac:

- Health: <http://127.0.0.1:8000/health> (should return `{"status":"ok"}`)
- Interactive API documentation: <http://127.0.0.1:8000/docs>

Keep this terminal open while using the API. Stop it with **Ctrl+C**. For a new terminal session, activate the environment again with `source .venv/bin/activate`.

**Security note:** `--host 0.0.0.0` exposes port 8000 to reachable interfaces, which is useful for an iPhone on the same network. Use only on a trusted network and do not expose the development server to the public internet.

## 3. Prepare the iPhone and Apple signing

### 3.1 Pair the device and enable Developer Mode

1. Unlock the iPhone and connect it to the Mac using a cable.
2. Tap **Trust This Computer** on the iPhone, if prompted, and enter its passcode.
3. In Xcode, open its device management window (for example **Window > Devices and Simulators** on some Xcode versions, or **Xcode > Open Developer Tool > Device Hub** on newer versions). Confirm that the iPhone is recognized.
4. On the iPhone go to **Settings > Privacy & Security > Developer Mode**, enable it, and follow the restart and confirmation prompts. If Developer Mode is not visible, finish pairing through Xcode first.
5. Keep the phone unlocked during the first installation and allow any additional trust or local-network prompts.

### 3.2 Add your Apple Account to Xcode

1. In **Xcode > Settings > Accounts** (sometimes labeled **Apple Accounts**), sign in with your Apple Account.
2. Xcode will show your enrolled development team, or a free **Personal Team** if you have no paid membership.
3. Allow **automatic signing**. For local device installs, Xcode can create and manage development certificates and provisioning profiles.

The app's bundle identifier is set in `apps/mobile/app.config.js`:

```text
com.jonasmaihoefer.roomtwin
```

If signing reports an identifier conflict, choose an identifier unique to your team, edit **that checked-in config file**, and commit the change. Do not rely on an uncommitted local override. Do not commit signing certificates, profiles, private keys, or account credentials.

## 4. First local native iOS build

Return to the mobile directory with the iPhone connected:

```bash
cd ~/Projects/room-twin/apps/mobile
npx expo run:ios --device
```

Choose the **physical iPhone** if prompted. Expo will generate the ignored `ios/` native project when it does not exist, install native dependencies, compile through the local Xcode toolchain, sign the development app, install it on the phone, and start the Metro development server.

If signing needs manual attention:

1. Run `npx expo prebuild --platform ios` if `ios/` does not exist yet.
2. Open the generated iOS workspace (the `.xcworkspace` file inside `apps/mobile/ios/`) in Xcode.
3. Select the **app target** and open **Signing & Capabilities**.
4. Enable **Automatically manage signing** and select the correct Apple **Team**.
5. Check the bundle identifier and the physical device as the run destination.
6. Build from Xcode to inspect the detailed native error, then retry `npx expo run:ios --device` if appropriate.

> The `ios/` directory is intentionally ignored by Git in this repository. It is generated output, **not** the source of truth. Keep persistent changes in Expo configuration or a config plugin so they survive regeneration.

**Success criteria:** The Room Twin app appears on the physical iPhone, starts without an immediate crash, and connects to Metro. Because RoomPlan has not yet been validated on hardware, installation alone does **not** prove that scanning/export works.

### 4.1 Verify a real RoomPlan scan

Use a safe test room and perform the following checks:

1. Open Room Twin on the iPhone, select **Start scan**, and grant Camera permission.
2. Move slowly through a room to capture walls and recognized objects.
3. Select **Finish scan**. Verify the scanner closes and the UI reports that JSON was loaded.
4. Inspect the displayed JSON; confirm it is labeled **Apple RoomPlan**, not a synthetic browser fixture.
5. If a USDZ path is shown, record that the file URL was returned. This is not yet proof that downstream geometry conversion works.
6. Use **Share JSON file** to validate the iOS share flow.
7. Start another scan; also test **Cancel**, restart, permission denial, and export-error handling.
8. Record the device model, iOS version, app commit, wrapper version, and any native logs/errors.

**Important:** RoomPlan capture/export is currently unverified. If this test fails, diagnose the native integration instead of assuming the browser mock proves correctness. Do not commit private scans or room layouts.

## 5. Network and API configuration

The provided example config is `apps/mobile/.env.example`:

```dotenv
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

`127.0.0.1` on a **physical iPhone** points to the iPhone, **not your Mac**. For future requests from the phone to a locally running backend, use the Mac's LAN IP instead.

1. Find the Mac's local IP address in **System Settings > Network**, or use `ipconfig getifaddr en0` if `en0` is the connected Wi-Fi interface (the interface name may differ).
2. Open `apps/mobile/.env`, created in section 2.4. If it does not exist, copy `.env.example` to `.env`.
3. Edit `.env` to your real LAN address, for example:

   ```dotenv
   EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
   ```

4. With the backend running, open `http://192.168.1.42:8000/health` in **Safari on the iPhone**. It should return `{"status":"ok"}`.
5. Restart Metro after changing `.env` if the new value does not appear in the app.

**Current behavior:** The Room Twin UI only *displays* the configured API URL. It does **not** upload scans or make requests to the backend yet. Verifying the health endpoint in Safari is a **network check**, not an end-to-end integration test.

If phone-to-backend requests are later implemented, account for iOS App Transport Security and local-network permissions. Prefer HTTPS for real deployments; do not add an unrestricted cleartext-network exception without reviewing its scope and security implications.

## 6. Daily development routine

After the one-time native install, you normally need **no new iOS build** for JavaScript/TypeScript/UI changes.

### Terminal A: backend (when working on API functionality)

```bash
cd ~/Projects/room-twin/backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Uvicorn's `--reload` picks up Python source changes. The backend does not have to run merely to test the existing on-device scan/JSON display, because upload is not implemented yet.

### Terminal B: Metro (normal mobile development)

```bash
cd ~/Projects/room-twin/apps/mobile
npm run start:dev-client -- --lan
```

Keep the iPhone and Mac on the same trusted network. Open the **installed Room Twin development app** on the iPhone and connect to the Metro server if it does not connect automatically. Change code in your editor; **Fast Refresh** will update most JavaScript/TypeScript and style edits without reinstalling the app.

For an occasional fresh start of Metro, stop it with **Ctrl+C** and run the same command again. If the bundler has stale cache issues, try:

```bash
npx expo start --dev-client --clear --lan
```

### When must I rebuild?

| Change | Action |
| --- | --- |
| React component, TypeScript, JS, styles, most app logic | **Metro / Fast Refresh only** |
| Python/FastAPI code | **Uvicorn auto-reload**; no mobile rebuild |
| `.env` or `EXPO_PUBLIC_*` value | Reload/restart Metro as needed; normally no native rebuild |
| New/updated native module, e.g. `expo-roomplan` | **Local native rebuild** |
| Native plugin, iOS permissions, deployment target, bundle identifier | **Regenerate native project as needed, then rebuild** |
| Expo SDK / React Native native-version upgrade | **Regenerate and rebuild**, then re-test RoomPlan |
| Personal Team profile expired | **Re-sign/reinstall** the local app |

Build again locally with:

```bash
cd ~/Projects/room-twin/apps/mobile
npx expo run:ios --device
```

When native configuration has changed and generated files may be stale, regenerate **only after reviewing whether any local native changes would be lost**:

```bash
cd ~/Projects/room-twin/apps/mobile
npx expo prebuild --platform ios --clean
npx expo run:ios --device
```

`--clean` removes and regenerates the native iOS project. Do not run it routinely for UI edits. Neither command consumes an EAS cloud-build quota.

## 7. Tests and checks before a PR

Run these from `apps/mobile`:

```bash
cd ~/Projects/room-twin/apps/mobile
npm run lint
npm run typecheck
npm test -- --ci
npx expo install --check
npx expo-doctor
npx expo config --type prebuild
npm run export:ios
npm run export:web
```

These commands check source, configuration, tests, and JavaScript bundles. **`npm run export:ios` is not a native Xcode compilation** and does not verify `expo-roomplan` on an iPhone.

Run the backend tests from `backend`:

```bash
cd ~/Projects/room-twin/backend
source .venv/bin/activate
python -m pytest
```

If your change affects RoomPlan, iOS permissions, export callbacks, file reading, or native sharing, also document a **real iPhone test**. Unit and web-mock tests are valuable but cannot replace this hardware check.

### Optional browser mock

You may run `npm run web` from `apps/mobile` to test shared UI, synthetic scan states, or browser behavior. This is an **optional test surface**, not a required development phase; it never provides real LiDAR capture.

## 8. Troubleshooting

| Symptom | What to check |
| --- | --- |
| `xcodebuild` not found, or Xcode license/setup errors | Open Xcode, complete setup, choose its Command Line Tools, and re-check `xcode-select -p`. |
| `pod` not found / native dependency installation fails | Check `pod --version`, CocoaPods installation, and Xcode version; retry native build after fixing the underlying issue. |
| No iPhone appears in device list | Unlock it, check cable/trust prompts, confirm Xcode recognizes it, and enable Developer Mode. |
| Signing / provisioning error | Add Apple Account to Xcode; choose the correct Team; enable automatic signing; verify bundle identifier; ensure free profiles have not expired. |
| App opens but cannot connect to Metro | Same trusted Wi-Fi, correct LAN interface, Mac firewall, local-network permission, and Metro running with `--lan`. Retry with a cable or debug via Xcode. |
| RoomPlan native module unavailable | Make sure this is the locally built **Room Twin development app**, not Expo Go. Rebuild after native package/plugin changes. |
| Camera or scan fails | Check camera permission, LiDAR compatibility, iOS version, the RoomPlan integration, and Xcode/device logs. |
| App finishes but returns no JSON | Inspect export/status callbacks and native logs. The wrapper has not yet been verified against real hardware. |
| Health URL works on Mac but not on iPhone | Use Mac **LAN IP**, not `localhost`; check both devices' network, firewall, and port 8000. |
| `.env` changes not visible | Verify `apps/mobile/.env` exists and restart Metro. |
| Build works in browser but fails on iOS | Browser uses a mock scanner; use the real native build/logs to diagnose. |

For native crashes or a hard-to-explain Xcode build error, open the generated `ios/*.xcworkspace` in Xcode, select the physical device, and inspect build errors or device logs. Generated native files are disposable: move necessary persistent changes into Expo config or plugins rather than relying on edits to `ios/`.

## 9. Security and data handling

- Treat real room scans, JSON exports, and USDZ files as sensitive: indoor layouts may reveal private information.
- Do not commit credentials, provisioning profiles, private keys, `.env`, or real/private scan captures.
- Only use approved, sanitized fixtures for tests and code review.
- Use a trusted development network, protect backend endpoints before real data upload, and plan HTTPS/authentication before remote access.
- Avoid committing generated `ios/` content; it is excluded by the existing `.gitignore`.

## 10. Quick reference

**First native build (once, then only after native changes):**

```bash
cd ~/Projects/room-twin/apps/mobile
npm ci
npx expo run:ios --device
```

**Everyday frontend development:**

```bash
cd ~/Projects/room-twin/apps/mobile
npm run start:dev-client -- --lan
```

**Everyday backend development:**

```bash
cd ~/Projects/room-twin/backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**No EAS cloud build is required** for any of those commands.

## Further reading

- [Room Twin architecture](../architecture/architecture.md)
- [Room Twin iOS/RoomPlan validation checklist](../testing/ios-roomplan-validation.md)
- [Expo: Local app compilation](https://docs.expo.dev/guides/local-app-development/)
- [Expo: CLI iOS device builds and signing](https://docs.expo.dev/more/expo-cli/)
- [Expo: iOS Developer Mode](https://docs.expo.dev/guides/ios-developer-mode/)
- [Apple: Running apps on physical devices](https://developer.apple.com/documentation/xcode/running-your-app-on-simulated-or-physical-devices)
- [Apple: Personal Team limitations](https://developer.apple.com/help/account/basics/about-your-developer-account)
