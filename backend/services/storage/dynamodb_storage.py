import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import boto3

from backend.models.schemas import (
    Recall,
    NormalizedRecall,
    InventoryItem,
    MatchResult,
)

logger = logging.getLogger("recallmatch.storage.dynamodb")


class DynamoDBStorageService:
    """Service to persist recall audit run metadata and audited item results in AWS DynamoDB."""

    def __init__(
        self,
        table_name: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        self.table_name = table_name or os.getenv("RECLARO_DYNAMODB_TABLE")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self._resource = None
        self._table = None

    def _get_table(self):
        if self._table is None:
            if self._resource is None:
                self._resource = boto3.resource("dynamodb", region_name=self.region_name)
            self._table = self._resource.Table(self.table_name)
        return self._table

    def save_audit_run(
        self,
        recall: Recall,
        normalized_recall: NormalizedRecall,
        inventory_items: List[InventoryItem],
        match_results: List[MatchResult],
        inventory_storage_key: str,
        confirmed_count: int,
        needs_review_count: int,
        not_affected_count: int,
    ) -> str:
        """
        Persists a recall audit run META record and individual ITEM records to DynamoDB.
        Returns the generated run_id UUID string.
        Raises RuntimeError if RECLARO_DYNAMODB_TABLE is not configured.
        """
        if not self.table_name:
            raise RuntimeError("RECLARO_DYNAMODB_TABLE environment variable is not configured.")

        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        # Build META record
        meta_record: Dict[str, Any] = {
            "pk": f"RUN#{run_id}",
            "sk": "META",
            "record_type": "RUN_META",
            "run_id": run_id,
            "recall_id": recall.recall_id,
            "recalling_firm": recall.recalling_firm,
            "normalized_recall": normalized_recall.model_dump(),
            "inventory_storage_key": inventory_storage_key,
            "created_at": created_at,
            "total_audited": len(inventory_items),
            "confirmed_count": confirmed_count,
            "needs_review_count": needs_review_count,
            "not_affected_count": not_affected_count,
        }

        # Index inventory items by inventory_id for fast lookup
        items_map = {item.inventory_id: item.model_dump() for item in inventory_items}

        item_records: List[Dict[str, Any]] = []
        for result in match_results:
            inv_id = result.inventory_id
            item_data = items_map.get(inv_id, {})
            item_record: Dict[str, Any] = {
                "pk": f"RUN#{run_id}",
                "sk": f"ITEM#{inv_id}",
                "record_type": "AUDITED_ITEM",
                "run_id": run_id,
                "inventory_id": inv_id,
                "recall_id": result.recall_id,
                "status": result.status.value if hasattr(result.status, "value") else str(result.status),
                "signals": result.signals,
                "evidence": result.evidence,
                "recommended_action": result.recommended_action,
                "inventory_item": item_data,
                "created_at": created_at,
            }
            item_records.append(item_record)

        all_records = [meta_record] + item_records

        logger.info(
            f"Persisting audit run to DynamoDB: table='{self.table_name}', "
            f"run_id='{run_id}', records={len(all_records)}"
        )

        table = self._get_table()
        with table.batch_writer() as batch:
            for record in all_records:
                batch.put_item(Item=record)

        return run_id
