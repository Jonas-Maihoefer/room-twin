# Architecture decision

**Chosen MVP path:** custom iOS app → Apple RoomPlan → structured scan data → direct backend API → furniture replacement → GLB download/share.

React Native with Expo/EAS is the Windows-friendly mobile candidate, FastAPI/Python is the backend, and a physical LiDAR-capable Apple device is required to validate scanning. These implementation technologies remain subject to the RoomPlan build and device proof described in [the architecture](architecture.md).

The initial executable foundation establishes Expo, a RoomPlan scan screen, JSON export inspection, and a small FastAPI API seam. The ingestion schema is explicitly provisional. The repository does not claim the scan-to-GLB workflow is complete.
