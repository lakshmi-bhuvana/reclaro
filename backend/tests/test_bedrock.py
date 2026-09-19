import os
from unittest.mock import MagicMock, patch
import pytest
from botocore.exceptions import NoCredentialsError, ClientError

from backend.models.schemas import InventoryItem, NormalizedRecall, MatchStatus
from backend.services.bedrock.bedrock_client import BedrockClient
from backend.services.bedrock.normalization_service import BedrockNormalizationService, BedrockNormalizationOutput
from backend.services.bedrock.candidate_service import BedrockCandidateService
from backend.services.matching.candidate_generator import SignalGenerator
from backend.services.verification.verifier import VerificationEngine
from backend.services.evidence.evidence_builder import EvidenceBuilder


@pytest.fixture
def sample_recall():
    return NormalizedRecall(
        recall_id="Z-1092-2024",
        manufacturer="Smith & Nephew Inc.",
        product_families=["JOURNEY II"],
        models=["JOURNEY-II-CR"],
        catalog_numbers=["74021-212"],
        lot_ranges=["LOT-55921"],
    )


def test_valid_structured_bedrock_response():
    """A. Test parsing of valid structured JSON from Bedrock model output without recall context."""
    mock_boto_client = MagicMock()
    mock_boto_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "text": """{
                            "normalized_manufacturer": "Smith & Nephew Inc.",
                            "normalized_product_name": "Journey II Total Knee",
                            "normalized_model": "JOURNEY-II-CR",
                            "normalized_catalog_number": "74021212",
                            "candidate_identifiers": ["74021-212"],
                            "candidate_product_family": "JOURNEY II",
                            "reasoning_summary": "Cleaned manufacturer and stripped hyphen from catalog number."
                        }"""
                    }
                ]
            }
        }
    }

    client = BedrockClient()
    client._client = mock_boto_client

    norm_service = BedrockNormalizationService(bedrock_client=client)
    item = InventoryItem(
        inventory_id="INV-2001",
        manufacturer="Smith & Nephew",
        product_name="Journey 2 Total Knee Component",
        catalog_number="74021212",
    )

    result = norm_service.normalize_item(item)
    assert result is not None
    assert result.normalized_manufacturer == "Smith & Nephew Inc."
    assert result.normalized_model == "JOURNEY-II-CR"
    assert "74021-212" in result.candidate_identifiers

    # Verify converse was called and prompt did NOT include recall reference context
    mock_boto_client.converse.assert_called_once()
    call_kwargs = mock_boto_client.converse.call_args.kwargs
    prompt_text = call_kwargs["messages"][0]["content"][0]["text"]
    assert "Recall Reference Context" not in prompt_text
    assert "Do NOT invent identifiers" in call_kwargs["system"][0]["text"]


def test_malformed_bedrock_json():
    """B. Test fallback handling when Bedrock returns malformed JSON."""
    mock_boto_client = MagicMock()
    mock_boto_client.converse.return_value = {
        "output": {
            "message": {
                "content": [{"text": "INVALID_JSON { manufacturer: 'Smith & Nephew' missing quotes"}]
            }
        }
    }

    client = BedrockClient()
    client._client = mock_boto_client

    norm_service = BedrockNormalizationService(bedrock_client=client)
    item = InventoryItem(
        inventory_id="INV-2002",
        manufacturer="Smith & Nephew",
        product_name="Knee Implant",
    )

    result = norm_service.normalize_item(item)
    assert result is None


def test_bedrock_unavailable():
    """C. Test fallback handling when Bedrock API encounters ClientError or exception."""
    mock_boto_client = MagicMock()
    mock_boto_client.converse.side_effect = ClientError(
        {"Error": {"Code": "ThrottlingException", "Message": "Rate limit exceeded"}},
        "converse"
    )

    client = BedrockClient()
    client._client = mock_boto_client

    norm_service = BedrockNormalizationService(bedrock_client=client)
    item = InventoryItem(
        inventory_id="INV-2003",
        manufacturer="Smith & Nephew",
        product_name="Knee Implant",
    )

    result = norm_service.normalize_item(item)
    assert result is None


def test_missing_aws_configuration():
    """D. Test fallback handling when AWS credentials or client setup fails."""
    mock_boto_client = MagicMock()
    mock_boto_client.converse.side_effect = NoCredentialsError()

    client = BedrockClient()
    client._client = mock_boto_client

    norm_service = BedrockNormalizationService(bedrock_client=client)
    item = InventoryItem(
        inventory_id="INV-2004",
        manufacturer="Smith & Nephew",
        product_name="Knee Implant",
    )

    result = norm_service.normalize_item(item)
    assert result is None


def test_candidate_identifiers_cannot_create_ai_catalog_candidate(sample_recall):
    """Test that candidate_identifiers alone CANNOT create AI_CATALOG_CANDIDATE."""
    mock_norm_service = MagicMock()
    mock_norm_service.normalize_item.return_value = BedrockNormalizationOutput(
        normalized_manufacturer="Smith & Nephew Inc.",
        normalized_catalog_number=None,  # No normalized_catalog_number
        candidate_identifiers=["74021-212"],  # Matching identifier in candidate_identifiers list
        reasoning_summary="Suggested candidate identifier only.",
    )

    candidate_service = BedrockCandidateService(normalization_service=mock_norm_service)

    item = InventoryItem(
        inventory_id="INV-2005",
        manufacturer="Smith & Nephew",
        product_name="Journey II CR Knee Component",
    )

    ai_signals = candidate_service.generate_candidate_signals(item, sample_recall)
    assert "AI_CATALOG_CANDIDATE" not in ai_signals


def test_normalized_catalog_number_creates_ai_catalog_candidate(sample_recall):
    """Test that normalized_catalog_number matching generates AI_CATALOG_CANDIDATE."""
    mock_norm_service = MagicMock()
    mock_norm_service.normalize_item.return_value = BedrockNormalizationOutput(
        normalized_manufacturer="Smith & Nephew Inc.",
        normalized_catalog_number="74021212",  # Matches recall catalog '74021-212'
        reasoning_summary="Stripped hyphen from catalog ref.",
    )

    candidate_service = BedrockCandidateService(normalization_service=mock_norm_service)

    item = InventoryItem(
        inventory_id="INV-2006",
        manufacturer="Smith & Nephew",
        product_name="Journey II CR Knee Component",
        catalog_number="REF-74021212",
    )

    ai_signals = candidate_service.generate_candidate_signals(item, sample_recall)
    assert "AI_CATALOG_CANDIDATE" in ai_signals
    assert "AI_MANUFACTURER_CANDIDATE" in ai_signals


def test_ai_candidate_results_in_needs_review_not_confirmed(sample_recall):
    """Invariant test: AI candidate evidence alone MUST result in NEEDS_REVIEW rather than CONFIRMED when deterministic proof is absent."""
    ai_signals = [
        "AI_MANUFACTURER_CANDIDATE",
        "AI_MODEL_CANDIDATE",
        "AI_CATALOG_CANDIDATE",
        "AI_PRODUCT_FAMILY_CANDIDATE",
    ]

    item = InventoryItem(
        inventory_id="INV-2007",
        manufacturer="Unknown Vendor",
        product_name="Unknown Device",
        model="UNKNOWN-MDL",
    )

    det_signals = SignalGenerator.evaluate_signals(item, sample_recall)
    assert "MANUFACTURER_MATCH" not in det_signals
    assert "EXACT_CATALOG_MATCH" not in det_signals
    assert "EXACT_MODEL_MATCH" not in det_signals

    status = VerificationEngine.verify(item, sample_recall, signals=det_signals + ai_signals)
    assert status == MatchStatus.NEEDS_REVIEW
    assert status != MatchStatus.CONFIRMED


def test_deterministic_exact_catalog_match_confirmed_when_bedrock_unavailable(sample_recall):
    """Test deterministic exact catalog match still results in CONFIRMED even if Bedrock returns no AI signals."""
    item = InventoryItem(
        inventory_id="INV-2008",
        manufacturer="Smith & Nephew Inc.",
        product_name="Journey II CR Knee",
        catalog_number="74021-212",
        lot_number="LOT-55921",
    )

    match_result = EvidenceBuilder.build_match_result(item, sample_recall, ai_signals=None)
    assert match_result.status == MatchStatus.CONFIRMED
    assert "CONFIRMED MATCH" in match_result.evidence


def test_wrong_manufacturer_remains_not_affected(sample_recall):
    """Test item with wrong manufacturer remains NOT_AFFECTED even if Bedrock suggested candidate catalog."""
    mock_norm_service = MagicMock()
    mock_norm_service.normalize_item.return_value = BedrockNormalizationOutput(
        normalized_manufacturer="ACME Supplies LLC",
        normalized_catalog_number="74021-212",
        reasoning_summary="Completely different manufacturer.",
    )

    candidate_service = BedrockCandidateService(normalization_service=mock_norm_service)

    item = InventoryItem(
        inventory_id="INV-2009",
        manufacturer="ACME Medical Supplies",
        product_name="Surgical Tray",
        catalog_number="99999-999",
    )

    ai_signals = candidate_service.generate_candidate_signals(item, sample_recall)
    assert "AI_MANUFACTURER_CANDIDATE" not in ai_signals

    match_result = EvidenceBuilder.build_match_result(item, sample_recall, ai_signals=ai_signals)
    assert match_result.status == MatchStatus.NOT_AFFECTED
    assert "NOT AFFECTED" in match_result.evidence
