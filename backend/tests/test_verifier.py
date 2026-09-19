from backend.models.schemas import InventoryItem, NormalizedRecall, MatchStatus
from backend.services.verification.verifier import VerificationEngine
from backend.services.evidence.evidence_builder import EvidenceBuilder


def test_verifier_confirmed_status_on_exact_catalog_and_lot():
    recall = NormalizedRecall(
        recall_id="Z-1092-2024",
        manufacturer="medtronic",
        models=["HVAD-100"],
        catalog_numbers=["HV100REF"],
        lot_ranges=["LOT2023A99"],
        serial_ranges=["SN884920"],
    )

    item = InventoryItem(
        inventory_id="INV-1001",
        manufacturer="Medtronic Inc.",
        product_name="Heartware Ventricular Assist System",
        model="HVAD-100",
        catalog_number="HV-100-REF",
        lot_number="LOT-2023-A99",
        serial_number="SN-884920",
    )

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.CONFIRMED

    result = EvidenceBuilder.build_match_result(item, recall)
    assert result.status == MatchStatus.CONFIRMED
    assert "CONFIRMED MATCH" in result.evidence
    assert "POTENTIALLY AFFECTED" in result.recommended_action


def test_verifier_needs_review_on_model_match_without_lot_proof():
    recall = NormalizedRecall(
        recall_id="Z-1092-2024",
        manufacturer="medtronic",
        models=["HVAD-100"],
        catalog_numbers=["HV100REF"],
        lot_ranges=["LOT2023A99"],
    )

    # Item has matching manufacturer and model, but a different or missing lot number
    item = InventoryItem(
        inventory_id="INV-1002",
        manufacturer="Medtronic Inc.",
        product_name="Heartware HVAD Controller",
        model="HVAD-100",
        catalog_number="HV-100-REF",
        lot_number="LOT-2024-UNKNOWN",
    )

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.NEEDS_REVIEW

    result = EvidenceBuilder.build_match_result(item, recall)
    assert result.status == MatchStatus.NEEDS_REVIEW
    assert "NEEDS REVIEW" in result.evidence


def test_verifier_not_affected_on_unrelated_item():
    recall = NormalizedRecall(
        recall_id="Z-1092-2024",
        manufacturer="medtronic",
        models=["HVAD-100"],
        catalog_numbers=["HV100REF"],
    )

    item = InventoryItem(
        inventory_id="INV-1014",
        manufacturer="General Hospital Supplies",
        product_name="Standard IV Pole Heavy Duty",
        model="IVP-HD",
        catalog_number="POLE-100",
    )

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.NOT_AFFECTED

    result = EvidenceBuilder.build_match_result(item, recall)
    assert result.status == MatchStatus.NOT_AFFECTED
    assert "NOT AFFECTED" in result.evidence
