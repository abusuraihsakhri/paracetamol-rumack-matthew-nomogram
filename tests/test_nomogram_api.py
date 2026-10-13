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
