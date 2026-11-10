from uuid import uuid4

from fastapi import FastAPI

from app.schemas import RoomPlanSourceV1, ScanAcceptedV1

app = FastAPI(title="Room Twin API", version="0.1.0")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scans", response_model=ScanAcceptedV1, status_code=202, tags=["scans"])
def accept_scan_stub(payload: RoomPlanSourceV1) -> ScanAcceptedV1:
    """Validate the provisional envelope; intentionally do not store or process it."""
    return ScanAcceptedV1(
        scan_id=uuid4(),
        schema_version=payload.schema_version,
        status="accepted-stub",
        message="Validated only; persistence and scan-to-GLB processing are not implemented.",
    )
