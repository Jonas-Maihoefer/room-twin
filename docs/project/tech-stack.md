## Mobile App

* **React Native (with Expo)**
* **Why this choice was made:** It allows you to build the app without needing a local macOS machine for daily coding. It also keeps your syntax and logic aligned with standard web development principles while providing robust bridges to native device hardware.


* **Apple RoomPlan (via `expo-roomplan`)**
* **Why this choice was made:** Apple's RoomPlan is proprietary and hardware-dependent; it requires native access to the iPhone's LiDAR sensor to parse parametric walls, surfaces, and furniture bounding boxes. This wrapper brings that capability smoothly into your React Native environment.


* **Three.js via React Three Fiber (`@react-three/fiber` & `@react-three/drei`)**
* **Why this choice was made:** It turns 3D manipulation into standard React state management. Once the room `.glb` file is downloaded, users can interactively move, rotate, scale, or edit objects using touch gestures, and re-export the modified scene entirely on-device.



---

## Server

* **Python with FastAPI**
* **Why this choice was made:** Python is the premier language for 3D math and geometry processing. FastAPI provides a lightning-fast, asynchronous endpoint structure to receive room scan uploads from the mobile app and return processed `.glb` files instantly without unnecessary overhead.


* **`trimesh` (Python)**
* **Why this choice was made:** By dropping `.blend` files, you completely eliminated the need to run heavy, unstable desktop software (like Blender) on your server. `trimesh` handles all server-side asset swapping, matrix transformations, and scene assembly purely through code, making the backend completely bulletproof and lightweight.



---

## Shared Data Standard (Client & Server)

* **glTF / Binary `.glb` (Exclusively)**
* **Why this choice was made:** It is the universal language of modern real-time 3D web and mobile engines. Using `.glb` exclusively ensures instant loading times in Three.js, seamless server-side merging via `trimesh`, and effortless sharing via the iOS native system share sheet.