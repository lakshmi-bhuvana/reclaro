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


def test_baxter_81158_missing_distribution_date_needs_review():
    """A. Exact UDI + Mfr + Model but missing distribution date -> NEVER CONFIRMED, returns NEEDS_REVIEW."""
    from datetime import date
    recall = NormalizedRecall(
        recall_id="81158",
        manufacturer="baxter healthcare corporation",
        models=["SPECTRUM IQ"],
        udi_di=["00085412610900"],
        serial_ranges=["ALL_SERIALS"],
        distribution_date_before=date(2018, 7, 9),
    )

    item = InventoryItem(
        inventory_id="INV-BAX-01",
        manufacturer="Baxter Healthcare Corporation",
        product_name="Spectrum IQ Infusion Pump",
        model="SPECTRUM IQ",
        udi_di="00085412610900",
        distribution_date=None,
    )

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.NEEDS_REVIEW


def test_baxter_81158_valid_pre_cutoff_date_confirmed():
    """B. Exact UDI + Mfr + Model and distribution_date before cutoff (2018-06-15 < 2018-07-09) -> CONFIRMED."""
    from datetime import date
    recall = NormalizedRecall(
        recall_id="81158",
        manufacturer="baxter healthcare corporation",
        models=["SPECTRUM IQ"],
        udi_di=["00085412610900"],
        serial_ranges=["ALL_SERIALS"],
        distribution_date_before=date(2018, 7, 9),
    )

    item = InventoryItem(
        inventory_id="INV-BAX-02",
        manufacturer="Baxter Healthcare Corporation",
        product_name="Spectrum IQ Infusion Pump",
        model="SPECTRUM IQ",
        udi_di="00085412610900",
        distribution_date=date(2018, 6, 15),
    )

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.CONFIRMED


# ---------------------------------------------------------------------------
# Adversarial coverage tests — catalog, UDI, model, product-family edge cases
# ---------------------------------------------------------------------------

def _make_cardio_recall():
    """Shared benchmark-style recall: Cardio Systems, Spectrum IQ, catalog range 74021210-74021229."""
    return NormalizedRecall(
        recall_id="ADV-CARDIO-001",
        manufacturer="cardio systems",
        product_families=["Spectrum IQ Infusion Pump", "Infusion Pump"],
        models=["SPECTRUM IQ"],
        catalog_numbers=[str(n) for n in range(74021210, 74021230)],
        lot_ranges=["ALL_LOTS"],
        serial_ranges=["ALL_SERIALS"],
    )


def test_correct_manufacturer_wrong_catalog_needs_review_via_family():
    """Correct mfr, catalog outside range, product name has family token -> NEEDS_REVIEW."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = _make_cardio_recall()
    item = InventoryItem(
        inventory_id="ADV-001",
        manufacturer="Cardio Systems Inc.",
        product_name="Spectrum IQ Infusion Pump Rental",
        catalog_number="99999999",  # outside recall catalog range
    )

    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "MANUFACTURER_MATCH" in signals
    assert "EXACT_CATALOG_MATCH" not in signals
    assert "PRODUCT_FAMILY_MATCH" in signals

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.NEEDS_REVIEW


def test_missing_catalog_product_family_token_overlap_needs_review():
    """No catalog, no model, mfr matches, product name overlaps with product family -> NEEDS_REVIEW."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = _make_cardio_recall()
    item = InventoryItem(
        inventory_id="ADV-002",
        manufacturer="Cardio Systems Inc.",
        product_name="Infusion Pump Unit",
        catalog_number=None,
        model=None,
    )

    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "MANUFACTURER_MATCH" in signals
    assert "EXACT_CATALOG_MATCH" not in signals
    assert "EXACT_MODEL_MATCH" not in signals
    assert "PRODUCT_FAMILY_MATCH" in signals

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.NEEDS_REVIEW


def test_wrong_udi_no_other_identifiers_not_affected():
    """Wrong UDI + wrong manufacturer -> NOT_AFFECTED."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = NormalizedRecall(
        recall_id="ADV-UDI-001",
        manufacturer="medtronic",
        udi_di=["00088888000001"],
        models=["MDT-X100"],
        catalog_numbers=["MDT100REF"],
    )
    item = InventoryItem(
        inventory_id="ADV-003",
        manufacturer="General Hospital Supplies",
        product_name="Generic IV Stand",
        udi_di="00099999000099",
    )

    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "EXACT_UDI_MATCH" not in signals
    assert "MANUFACTURER_MATCH" not in signals

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.NOT_AFFECTED


def test_exact_model_match_without_catalog_confirmed():
    """Mfr + exact model match is sufficient for CONFIRMED even when catalog is absent (Rule 1, model branch)."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = _make_cardio_recall()
    item = InventoryItem(
        inventory_id="ADV-004",
        manufacturer="Cardio Systems Inc.",
        product_name="Spectrum IQ Infusion Pump",
        model="Spectrum IQ",
        catalog_number=None,
    )

    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "MANUFACTURER_MATCH" in signals
    assert "EXACT_MODEL_MATCH" in signals
    assert "EXACT_CATALOG_MATCH" not in signals

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.CONFIRMED


def test_fuzzy_partial_model_does_not_confirm():
    """FUZZY_MODEL_MATCH alone must NOT produce CONFIRMED; must be NEEDS_REVIEW when mfr matches."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = NormalizedRecall(
        recall_id="ADV-FUZZY-001",
        manufacturer="medtronic",
        models=["HVAD-100"],
        catalog_numbers=["HV100REF"],
    )
    item = InventoryItem(
        inventory_id="ADV-005",
        manufacturer="Medtronic Inc.",
        product_name="HVAD Heart Pump",
        model="HVAD",  # substring of 'HVAD-100' -> FUZZY_MODEL_MATCH (len >= 3)
        catalog_number=None,
    )

    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "MANUFACTURER_MATCH" in signals
    assert "FUZZY_MODEL_MATCH" in signals
    assert "EXACT_MODEL_MATCH" not in signals

    status = VerificationEngine.verify(item, recall)
    assert status != MatchStatus.CONFIRMED
    assert status == MatchStatus.NEEDS_REVIEW


def test_baxter_81158_post_cutoff_date_not_confirmed():
    """C. Exact UDI + Mfr + Model but distribution_date on/after cutoff (2018-07-20 >= 2018-07-09) -> NOT CONFIRMED."""
    from datetime import date
    recall = NormalizedRecall(
        recall_id="81158",
        manufacturer="baxter healthcare corporation",
        models=["SPECTRUM IQ"],
        udi_di=["00085412610900"],
        serial_ranges=["ALL_SERIALS"],
        distribution_date_before=date(2018, 7, 9),
    )

    item = InventoryItem(
        inventory_id="INV-BAX-03",
        manufacturer="Baxter Healthcare Corporation",
        product_name="Spectrum IQ Infusion Pump",
        model="SPECTRUM IQ",
        udi_di="00085412610900",
        distribution_date=date(2018, 7, 20),
    )

    status = VerificationEngine.verify(item, recall)
    assert status != MatchStatus.CONFIRMED


# ---------------------------------------------------------------------------
# Serial signal contract tests
# ---------------------------------------------------------------------------

def _make_serial_recall(serial_ranges):
    return NormalizedRecall(
        recall_id="SN-TEST-001",
        manufacturer="acme medical",
        models=["PUMP-X"],
        catalog_numbers=["PXREF"],
        serial_ranges=serial_ranges,
    )


def _make_serial_item(serial_number):
    return InventoryItem(
        inventory_id="INV-SN-01",
        manufacturer="Acme Medical Inc.",
        product_name="Acme Pump X",
        model="PUMP-X",
        catalog_number="PX-REF",
        serial_number=serial_number,
    )


def test_all_serials_emits_serial_scope_all():
    """ALL_SERIALS in recall.serial_ranges must produce SERIAL_SCOPE_ALL when the item has a serial."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = _make_serial_recall(["ALL_SERIALS"])
    item = _make_serial_item("SN-999")
    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "SERIAL_SCOPE_ALL" in signals


def test_all_serials_does_not_emit_exact_serial_match():
    """ALL_SERIALS must NOT produce EXACT_SERIAL_MATCH — scope != value match."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = _make_serial_recall(["ALL_SERIALS"])
    item = _make_serial_item("SN-999")
    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "EXACT_SERIAL_MATCH" not in signals


def test_specific_serial_hit_emits_exact_serial_match():
    """When the inventory serial exactly matches a listed serial, emit EXACT_SERIAL_MATCH (not SERIAL_SCOPE_ALL)."""
    from backend.services.matching.candidate_generator import SignalGenerator

    recall = _make_serial_recall(["SN-001", "SN-002", "SN-999"])
    item = _make_serial_item("SN-999")
    signals = SignalGenerator.evaluate_signals(item, recall)
    assert "EXACT_SERIAL_MATCH" in signals
    assert "SERIAL_SCOPE_ALL" not in signals


def test_all_serials_verification_outcome_unchanged():
    """Verification rules (CONFIRMED/NEEDS_REVIEW/NOT_AFFECTED) must be unaffected by the signal rename.

    Recall has ALL_SERIALS scope → serial_scope_satisfied = True in verifier.
    Item matches mfr + exact catalog → result should still be CONFIRMED.
    """
    recall = _make_serial_recall(["ALL_SERIALS"])
    # Give the recall a catalog number so CONFIRMED is reachable
    recall.catalog_numbers = ["PXREF"]
    item = _make_serial_item("SN-ANY")
    item.manufacturer = "Acme Medical Inc."
    item.catalog_number = "PX-REF"

    status = VerificationEngine.verify(item, recall)
    assert status == MatchStatus.CONFIRMED

