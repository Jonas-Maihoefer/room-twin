import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURE = Path(__file__).parent / "fixtures" / "scan_ingest_v1.json"


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_ingestion_stub_accepts_versioned_envelope_without_claiming_processing() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    response = client.post("/scans", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["schema_version"] == "room-twin.scan-ingest.v1"
    assert body["status"] == "accepted-stub"
    assert "not implemented" in body["message"]
    assert body["scan_id"]


def test_scan_rejects_unknown_envelope_fields_and_empty_source() -> None:
    response = client.post(
        "/scans",
        json={
            "schema_version": "room-twin.scan-ingest.v1",
            "source_format": "apple-roomplan-json",
            "source_payload": {},
            "unexpected": True,
        },
    )
    assert response.status_code == 422
