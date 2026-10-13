from fastapi.testclient import TestClient
from agents.api import app

client = TestClient(app)


def test_api_nomogram():
    res = client.post("/api/nomogram", json={
        "hours_post_ingestion": 8,
        "concentration_mcg_ml": 75,
    })
    assert res.status_code == 200
    assert res.json()["status"] == "at_or_above_treatment_line"


def test_api_rejects_nonfinite_and_negative():
    for value in [-1, "NaN"]:
        res = client.post("/api/nomogram", json={
            "hours_post_ingestion": 8,
            "concentration_mcg_ml": value,
        })
        assert res.status_code == 422


def test_api_not_applicable():
    res = client.post("/api/nomogram", json={
        "hours_post_ingestion": 2,
        "concentration_mcg_ml": 100,
    })
    assert res.json()["status"] == "not_applicable"

def test_sensitive_identifier_rejected_without_server_error():
    res = client.post("/api/chat", json={"query": "Patient MRN-12345678"})
    assert res.status_code == 400
    assert res.json()["detail"] == "Sensitive identifier rejected"


def test_legacy_payload_rejects_nonfinite():
    res = client.post("/api/audit", json={
        "task_id": "T", "target_identifier": "KEY",
        "primary_metric": "NaN"
    })
    assert res.status_code == 422
