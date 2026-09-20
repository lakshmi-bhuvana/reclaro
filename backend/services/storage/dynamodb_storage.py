import os
import uuid
import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
import boto3
from boto3.dynamodb.conditions import Key, Attr

from backend.models.schemas import (
    Recall,
    NormalizedRecall,
    InventoryItem,
    MatchResult,
)

logger = logging.getLogger("recallmatch.storage.dynamodb")


def serialize_for_dynamodb(val: Any) -> Any:
    """
    Recursively converts Python objects into DynamoDB-safe representations.
    Specifically serializes datetime.date and datetime.datetime to ISO-8601 strings.
    """
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    elif isinstance(val, dict):
        return {k: serialize_for_dynamodb(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [serialize_for_dynamodb(v) for v in val]
    elif isinstance(val, tuple):
        return [serialize_for_dynamodb(v) for v in val]
    elif isinstance(val, set):
        return {serialize_for_dynamodb(v) for v in val}
    return val


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
            "normalized_recall": serialize_for_dynamodb(normalized_recall.model_dump()),
            "inventory_storage_key": inventory_storage_key,
            "created_at": created_at,
            "total_audited": len(inventory_items),
            "confirmed_count": confirmed_count,
            "needs_review_count": needs_review_count,
            "not_affected_count": not_affected_count,
        }

        # Index inventory items by inventory_id for fast lookup
        items_map = {
            item.inventory_id: serialize_for_dynamodb(item.model_dump())
            for item in inventory_items
        }

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

        all_records = [serialize_for_dynamodb(record) for record in [meta_record] + item_records]

        logger.info(
            f"Persisting audit run to DynamoDB: table='{self.table_name}', "
            f"run_id='{run_id}', records={len(all_records)}"
        )

        table = self._get_table()
        with table.batch_writer() as batch:
            for record in all_records:
                batch.put_item(Item=record)

        return run_id

    def list_audit_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Returns recent RUN_META records sorted descending by created_at.
        Queries the AuditRunIndex GSI on record_type='RUN_META' with ScanIndexForward=False.
        Returns clean product-level dicts (no pk/sk internal keys).
        Raises RuntimeError if table is not configured.
        """
        if not self.table_name:
            raise RuntimeError("RECLARO_DYNAMODB_TABLE environment variable is not configured.")

        table = self._get_table()
        query_kwargs: Dict[str, Any] = {
            "IndexName": "AuditRunIndex",
            "KeyConditionExpression": Key("record_type").eq("RUN_META"),
            "ScanIndexForward": False,
        }
        if limit:
            query_kwargs["Limit"] = limit

        response = table.query(**query_kwargs)
        items = response.get("Items", [])

        # Strip DynamoDB internal pk/sk before returning
        clean_items = []
        for rec in items:
            clean = {k: v for k, v in rec.items() if k not in ("pk", "sk")}
            clean_items.append(clean)

        return clean_items[:limit]

    def get_audit_run(
        self, run_id: str
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns (meta_record, item_records) for the given run_id.
        meta_record is None if run not found.
        item_records are clean product-level dicts (no pk/sk).
        Raises RuntimeError if table is not configured.
        """
        if not self.table_name:
            raise RuntimeError("RECLARO_DYNAMODB_TABLE environment variable is not configured.")

        table = self._get_table()
        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"RUN#{run_id}"),
        )
        all_records = response.get("Items", [])

        meta = None
        items = []
        for rec in all_records:
            # Strip DynamoDB internal pk/sk before returning
            clean = {k: v for k, v in rec.items() if k not in ("pk", "sk")}
            if rec.get("record_type") == "RUN_META":
                meta = clean
            elif rec.get("record_type") == "AUDITED_ITEM":
                items.append(clean)

        return meta, items
