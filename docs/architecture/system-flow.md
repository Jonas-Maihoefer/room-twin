# System flow

The chosen MVP flow is described in [the system architecture](architecture.md):

1. The custom iOS app starts an Apple RoomPlan capture.
2. RoomPlan exports structured JSON (and optionally USDZ) to a local file.
3. An explicit, versioned adapter will send scan data to the backend API.
4. The backend will replace selected furniture and produce a GLB for download/share.

Only steps 1–2 are represented in the mobile foundation, and they still require a real device test. The backend currently validates an opaque, provisional v1 source envelope and returns a stub response. Steps 3–4 are not yet implemented. See [the Windows guide](../development/windows.md) for build and verification steps.
