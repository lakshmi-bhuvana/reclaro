from backend.services.normalization.normalizer import TextNormalizer


def test_normalize_manufacturer_removes_suffixes():
    assert TextNormalizer.normalize_manufacturer("Medtronic Inc.") == "medtronic"
    assert TextNormalizer.normalize_manufacturer("Baxter Healthcare Corporation") == "baxter"
    assert TextNormalizer.normalize_manufacturer("Stryker Medical Systems LLC") == "stryker"
    assert TextNormalizer.normalize_manufacturer("Becton Dickinson (BD) USA") == "becton dickinson bd"


def test_normalize_code_strips_punctuation_and_spaces():
    assert TextNormalizer.normalize_code("HV-100-REF") == "HV100REF"
    assert TextNormalizer.normalize_code("99577-000 001") == "99577000001"
    assert TextNormalizer.normalize_code("  sn / 884-920  ") == "SN884920"


def test_extract_tokens_filters_stop_words():
    tokens = TextNormalizer.extract_tokens("Spectrum IQ Infusion Pump Unit with REF IQ-200")
    assert "spectrum" in tokens
    assert "infusion" in tokens
    assert "pump" not in tokens  # 'pump' is in stop words
    assert "with" not in tokens
