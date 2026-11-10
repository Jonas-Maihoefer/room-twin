from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomPlanSourceV1(BaseModel):
    """Versioned transport envelope. source_payload remains Apple data verbatim."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["room-twin.scan-ingest.v1"]
    source_format: Literal["apple-roomplan-json"]
    source_payload: dict[str, Any] = Field(min_length=1)


class ScanAcceptedV1(BaseModel):
    scan_id: UUID
    schema_version: Literal["room-twin.scan-ingest.v1"]
    status: Literal["accepted-stub"]
    message: str
