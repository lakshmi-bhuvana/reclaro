from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "RecallMatch Engine" in data["service"]


def test_list_recalls_endpoint():
    response = client.get("/api/recalls?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "recalls" in data
    assert len(data["recalls"]) > 0
    assert data["recalls"][0]["recall_id"] is not None


@patch("backend.api.main.s3_storage_service.upload_inventory_csv")
def test_match_inventory_endpoint(mock_s3_upload):
    mock_s3_upload.return_value = "inventory/uuid-1234/test_inventory.csv"

    # Fetch available recall id
    recalls_res = client.get("/api/recalls?limit=1")
    recall_id = recalls_res.json()["recalls"][0]["recall_id"]

    csv_data = (
        "inventory_id,manufacturer,product_name,model,catalog_number,lot_number\n"
        "INV-TEST1,Medtronic Inc.,Heartware System,HVAD-100,HV-100-REF,LOT-2023-A99\n"
        "INV-TEST2,General Supplies,IV Pole,POLE-1,,LOT-99\n"
    )

    files = {"file": ("test_inventory.csv", csv_data, "text/csv")}
    data = {"recall_id": recall_id}

    response = client.post("/api/match", data=data, files=files)
    assert response.status_code == 200
    result = response.json()

    assert result["total_audited"] == 2
    assert result["inventory_storage_key"] == "inventory/uuid-1234/test_inventory.csv"
    assert "results" in result
    assert len(result["results"]) == 2


@patch("backend.api.main.s3_storage_service.upload_inventory_csv")
def test_match_inventory_endpoint_s3_failure(mock_s3_upload):
    mock_s3_upload.side_effect = RuntimeError("RECLARO_S3_BUCKET environment variable is not configured.")

    recalls_res = client.get("/api/recalls?limit=1")
    recall_id = recalls_res.json()["recalls"][0]["recall_id"]

    csv_data = "inventory_id,manufacturer,product_name\nINV-1,Medtronic,Pump\n"
    files = {"file": ("test_inventory.csv", csv_data, "text/csv")}
    data = {"recall_id": recall_id}

    response = client.post("/api/match", data=data, files=files)
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "Inventory storage service is unavailable" in detail
