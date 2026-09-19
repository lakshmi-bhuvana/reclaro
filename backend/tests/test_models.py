import pytest
from pydantic import ValidationError
from backend.models.schemas import Recall, NormalizedRecall, InventoryItem, MatchResult, MatchStatus


def test_recall_model_instantiation():
    recall = Recall(
        recall_id="Z-100-2024",
        recalling_firm="Medtronic Inc.",
        product_description="Heartware HVAD System",
        classification="Class I",
    )
    assert recall.recall_id == "Z-100-2024"
    assert recall.recalling_firm == "Medtronic Inc."
    assert recall.classification == "Class I"


def test_inventory_item_defaults():
    item = InventoryItem(
        inventory_id="INV-001",
        manufacturer="Baxter Healthcare",
        product_name="Spectrum IQ Pump",
        model="SPEC-IQ-200",
    )
    assert item.inventory_id == "INV-001"
    assert item.quantity == 1
    assert item.location is None


def test_match_result_valid_status():
    res = MatchResult(
        inventory_id="INV-001",
        recall_id="Z-100-2024",
        status=MatchStatus.CONFIRMED,
        signals=["EXACT_CATALOG_MATCH"],
        evidence="Matches on catalog REF HV-100-REF",
        recommended_action="Quarantine item",
    )
    assert res.status == MatchStatus.CONFIRMED
    assert "EXACT_CATALOG_MATCH" in res.signals
