import pytest
from unittest.mock import MagicMock, patch
from backend.services.storage.s3_storage import S3StorageService


def test_missing_bucket_raises_runtime_error():
    """Test that calling upload_inventory_csv without RECLARO_S3_BUCKET raises RuntimeError."""
    service = S3StorageService(bucket_name=None)
    with pytest.raises(RuntimeError) as exc_info:
        service.upload_inventory_csv(b"col1,col2\nval1,val2", "test.csv")
    assert "RECLARO_S3_BUCKET environment variable is not configured" in str(exc_info.value)


@patch("boto3.client")
def test_upload_calls_put_object_and_returns_valid_key(mock_boto_client):
    """Test that upload_inventory_csv calls put_object with text/csv and returns object key starting with inventory/."""
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    service = S3StorageService(bucket_name="my-reclaro-inventory-bucket", region_name="us-east-1")
    csv_bytes = b"inventory_id,manufacturer,product_name\nINV-001,Medtronic,Pump"
    filename = "hospital_inventory_2026.csv"

    returned_key = service.upload_inventory_csv(csv_bytes, filename)

    assert returned_key.startswith("inventory/")
    assert returned_key.endswith("/hospital_inventory_2026.csv")

    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args.kwargs
    assert call_kwargs["Bucket"] == "my-reclaro-inventory-bucket"
    assert call_kwargs["Key"] == returned_key
    assert call_kwargs["Body"] == csv_bytes
    assert call_kwargs["ContentType"] == "text/csv"


@patch("boto3.client")
def test_filename_path_traversal_sanitization(mock_boto_client):
    """Test that filename path traversal attempts like ../../inventory.csv are sanitized."""
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3

    service = S3StorageService(bucket_name="my-reclaro-inventory-bucket")
    csv_bytes = b"inventory_id\nINV-1"
    traversal_filename = "../../dangerous_path/../../inventory.csv"

    returned_key = service.upload_inventory_csv(csv_bytes, traversal_filename)

    assert returned_key.startswith("inventory/")
    assert ".." not in returned_key
    assert "dangerous_path" not in returned_key
    assert returned_key.endswith("/inventory.csv")
