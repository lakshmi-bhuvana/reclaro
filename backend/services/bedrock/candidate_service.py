import logging
from typing import List, Optional

from backend.models.schemas import InventoryItem, NormalizedRecall
from backend.services.bedrock.normalization_service import BedrockNormalizationService
from backend.services.normalization.normalizer import TextNormalizer

logger = logging.getLogger("recallmatch.bedrock.candidate")


class BedrockCandidateService:
    """Generates candidate signals based on Bedrock normalization output."""

    def __init__(self, normalization_service: Optional[BedrockNormalizationService] = None):
        self.normalization_service = normalization_service or BedrockNormalizationService()

    def generate_candidate_signals(
        self,
        item: InventoryItem,
        recall: NormalizedRecall,
    ) -> List[str]:
        """
        Uses Bedrock normalization output to detect candidate alignment signals.
        Returns a list of AI candidate signals.
        """
        signals: List[str] = []

        norm_output = self.normalization_service.normalize_item(item)
        if not norm_output:
            return signals

        # 1. AI Manufacturer Candidate Signal
        if norm_output.normalized_manufacturer:
            ai_mfr = TextNormalizer.normalize_manufacturer(norm_output.normalized_manufacturer)
            recall_mfr = TextNormalizer.normalize_manufacturer(recall.manufacturer)

            if ai_mfr and recall_mfr:
                if ai_mfr in recall_mfr or recall_mfr in ai_mfr:
                    signals.append("AI_MANUFACTURER_CANDIDATE")
                else:
                    ai_mfr_tokens = TextNormalizer.extract_tokens(ai_mfr)
                    recall_mfr_tokens = TextNormalizer.extract_tokens(recall_mfr)
                    if ai_mfr_tokens and recall_mfr_tokens and (ai_mfr_tokens & recall_mfr_tokens):
                        signals.append("AI_MANUFACTURER_CANDIDATE")

        # 2. AI Model Candidate Signal
        if norm_output.normalized_model and recall.models:
            ai_model = norm_output.normalized_model.upper().strip()
            for r_model in recall.models:
                norm_r_model = r_model.upper().strip()
                if (
                    ai_model == norm_r_model
                    or TextNormalizer.normalize_code(ai_model) == TextNormalizer.normalize_code(norm_r_model)
                    or (len(ai_model) >= 3 and (ai_model in norm_r_model or norm_r_model in ai_model))
                ):
                    signals.append("AI_MODEL_CANDIDATE")
                    break

        # 3. AI Catalog Candidate Signal (Generated strictly from normalized_catalog_number)
        if norm_output.normalized_catalog_number and recall.catalog_numbers:
            ai_cat = TextNormalizer.normalize_code(norm_output.normalized_catalog_number)
            if ai_cat:
                for r_cat in recall.catalog_numbers:
                    norm_r_cat = TextNormalizer.normalize_code(r_cat)
                    if ai_cat == norm_r_cat or (len(ai_cat) >= 4 and (ai_cat in norm_r_cat or norm_r_cat in ai_cat)):
                        signals.append("AI_CATALOG_CANDIDATE")
                        break

        # 4. AI Product Family Candidate Signal
        if norm_output.candidate_product_family and recall.product_families:
            ai_family_tokens = TextNormalizer.extract_tokens(norm_output.candidate_product_family)
            if ai_family_tokens:
                for family in recall.product_families:
                    family_tokens = TextNormalizer.extract_tokens(family)
                    if family_tokens and (ai_family_tokens & family_tokens):
                        signals.append("AI_PRODUCT_FAMILY_CANDIDATE")
                        break

        return signals
