from datetime import date
from backend.models.schemas import Recall
from backend.services.recall_parser.parser import RecallParser


def test_parser_extracts_structured_scope():
    raw_recall = Recall(
        recall_id="Z-1092-2024",
        recalling_firm="Medtronic Inc.",
        product_description="Heartware Ventricular Assist System (HVAD) Pump. Model HVAD-100. REF HV-100-REF.",
        classification="Class I",
        code_info="Catalog REF HV-100-REF, Lot LOT-2023-A99. Serial SN-884920. UDI-DI 00643169876543.",
    )

    norm = RecallParser.parse(raw_recall)

    assert norm.recall_id == "Z-1092-2024"
    assert norm.manufacturer == "medtronic"
    assert "HVAD-100" in norm.models
    assert "HV100REF" in norm.catalog_numbers
    assert "00643169876543" in norm.udi_di
    assert "LOT2023A99" in norm.lot_ranges
    assert "SN884920" in norm.serial_ranges
    assert "Ventricular Assist" in norm.product_families


def test_parser_extracts_baxter_81158_distribution_scope():
    raw_recall = Recall(
        recall_id="81158",
        recalling_firm="Baxter Healthcare Corporation",
        product_description="Spectrum IQ Infusion Pump with Wireless Communication. Model SPECTRUM IQ.",
        classification="Class I",
        code_info="UDI 00085412610900 All Serial Numbers distributed prior to 07/09/2018",
    )

    norm = RecallParser.parse(raw_recall)

    assert "00085412610900" in norm.udi_di
    assert "ALL_SERIALS" in norm.serial_ranges
    assert norm.distribution_date_before == date(2018, 7, 9)
