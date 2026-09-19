import pytest
import uuid
from unittest.mock import MagicMock, patch
from backend.models.schemas import (
    Recall,
    NormalizedRecall,
    InventoryItem,
    MatchResult,
    MatchStatus,
)
from backend.services.storage.dynamodb_storage import DynamoDBStorageService


@pytest.fixture
def sample_audit_data():
    recall = Recall(
        recall_id="Z-1092-2024",
        recalling_firm="Medtronic Inc.",
        product_description="Heartware HVAD Controller",
        product_code="K999",
        classification="Class I",
    )
    normalized_recall = NormalizedRecall(
        recall_id="Z-1092-2024",
        manufacturer="medtronic",
        models=["HVAD-100"],
        catalog_numbers=["HV100REF"],
        lot_ranges=["LOT2023A99"],
    )
    items = [
        InventoryItem(
            inventory_id="INV-1001",
            manufacturer="Medtronic Inc.",
            product_name="Heartware HVAD",
            model="HVAD-100",
            catalog_number="HV-100-REF",
            lot_number="LOT-2023-A99",
        ),
        InventoryItem(
            inventory_id="INV-1002",
            manufacturer="General Supplies",
            product_name="IV Pole",
        ),
    ]
    results = [
        MatchResult(
            inventory_id="INV-1001",
            recall_id="Z-1092-2024",
            status=MatchStatus.CONFIRMED,
            signals=["MANUFACTURER_MATCH", "EXACT_CATALOG_MATCH"],
            evidence="CONFIRMED MATCH: Item INV-1001 matches FDA recall.",
            recommended_action="POTENTIALLY AFFECTED: Follow instructions.",
        ),
        MatchResult(
            inventory_id="INV-1002",
            recall_id="Z-1092-2024",
            status=MatchStatus.NOT_AFFECTED,
            signals=[],
            evidence="NOT AFFECTED: Item INV-1002 does not match.",
            recommended_action="No recall evidence found.",
        ),
    ]
    return recall, normalized_recall, items, results


def test_missing_dynamodb_table_raises_runtime_error(sample_audit_data):
    """Test that save_audit_run raises RuntimeError if RECLARO_DYNAMODB_TABLE is missing."""
    recall, normalized_recall, items, results = sample_audit_data
    service = DynamoDBStorageService(table_name=None)

    with pytest.raises(RuntimeError) as exc_info:
        service.save_audit_run(
            recall=recall,
            normalized_recall=normalized_recall,
            inventory_items=items,
            match_results=results,
            inventory_storage_key="inventory/uuid-1/test.csv",
            confirmed_count=1,
            needs_review_count=0,
            not_affected_count=1,
        )
    assert "RECLARO_DYNAMODB_TABLE environment variable is not configured" in str(exc_info.value)


@patch("boto3.resource")
def test_save_audit_run_writes_meta_and_item_records(mock_boto_resource, sample_audit_data):
    """Test that save_audit_run persists META and ITEM records into DynamoDB batch writer."""
    recall, normalized_recall, items, results = sample_audit_data

    mock_batch = MagicMock()
    mock_batch_ctx = MagicMock()
    mock_batch_ctx.__enter__.return_value = mock_batch

    mock_table = MagicMock()
    mock_table.batch_writer.return_value = mock_batch_ctx
    mock_boto_resource.return_value.Table.return_value = mock_table

    service = DynamoDBStorageService(table_name="my-reclaro-audit-table", region_name="us-east-1")

    run_id = service.save_audit_run(
        recall=recall,
        normalized_recall=normalized_recall,
        inventory_items=items,
        match_results=results,
        inventory_storage_key="inventory/uuid-9999/test.csv",
        confirmed_count=1,
        needs_review_count=0,
        not_affected_count=1,
    )

    # Verify run_id is a valid UUID
    uuid_obj = uuid.UUID(run_id)
    assert str(uuid_obj) == run_id

    # Verify put_item calls in batch: 1 META record + 2 ITEM records = 3 put_item calls
    assert mock_batch.put_item.call_count == 3

    written_items = [call.kwargs["Item"] for call in mock_batch.put_item.call_args_list]

    # Find META record
    meta_records = [r for r in written_items if r["sk"] == "META"]
    assert len(meta_records) == 1
    meta = meta_records[0]
    assert meta["pk"] == f"RUN#{run_id}"
    assert meta["record_type"] == "RUN_META"
    assert meta["recall_id"] == "Z-1092-2024"
    assert meta["recalling_firm"] == "Medtronic Inc."
    assert meta["inventory_storage_key"] == "inventory/uuid-9999/test.csv"
    assert meta["total_audited"] == 2
    assert meta["confirmed_count"] == 1
    assert "T" in meta["created_at"]

    # Find ITEM records
    item_records = [r for r in written_items if r["sk"].startswith("ITEM#")]
    assert len(item_records) == 2

    inv_1001 = next(r for r in item_records if r["sk"] == "ITEM#INV-1001")
    assert inv_1001["status"] == "CONFIRMED"
    assert inv_1001["inventory_item"]["manufacturer"] == "Medtronic Inc."
    assert "MANUFACTURER_MATCH" in inv_1001["signals"]
