
from typing import List, Tuple, Optional

from backend.models.schemas import (
    InventoryItem,
    NormalizedRecall,
    MatchStatus,
    MatchResult,
)
from backend.services.matching.candidate_generator import SignalGenerator
from backend.services.verification.verifier import VerificationEngine


class EvidenceBuilder:
    """Generates concise, human-readable evidence summaries and recommended actions for biomedical staff."""

    @staticmethod
    def build_match_result(
        item: InventoryItem,
        recall: NormalizedRecall,
        ai_signals: Optional[List[str]] = None,
    ) -> MatchResult:
        signals = SignalGenerator.evaluate_signals(item, recall, ai_signals=ai_signals)
        status = VerificationEngine.verify(item, recall, signals=signals)

        evidence, recommended_action = EvidenceBuilder._generate_explanation(
            item,
            recall,
            status,
            signals,
        )

        return MatchResult(
            inventory_id=item.inventory_id,
            recall_id=recall.recall_id,
            status=status,
            signals=signals,
            evidence=evidence,
            recommended_action=recommended_action,
        )

    @staticmethod
    def _generate_explanation(
        item: InventoryItem,
        recall: NormalizedRecall,
        status: MatchStatus,
        signals: List[str],
    ) -> Tuple[str, str]:

        if status == MatchStatus.CONFIRMED:
            matched_items = []

            if "EXACT_UDI_MATCH" in signals:
                matched_items.append(
                    f"UDI-DI '{item.udi_di}'"
                )

            if "EXACT_CATALOG_MATCH" in signals:
                matched_items.append(
                    f"Catalog REF '{item.catalog_number}'"
                )

            if "EXACT_MODEL_MATCH" in signals:
                matched_items.append(
                    f"Model '{item.model}'"
                )

            if (
                "EXACT_LOT_MATCH" in signals
                or "LOT_MATCH_ALL" in signals
            ):
                matched_items.append(
                    f"Lot '{item.lot_number}'"
                )

            if (
                "EXACT_SERIAL_MATCH" in signals
                or "SERIAL_MATCH_ALL" in signals
            ):
                matched_items.append(
                    f"Serial '{item.serial_number}'"
                )

            details = (
                ", ".join(matched_items)
                if matched_items
                else "Deterministic parameters"
            )

            evidence = (
                f"CONFIRMED MATCH: Item {item.inventory_id} "
                f"({item.product_name}) from '{item.manufacturer}' "
                f"deterministically matches FDA Recall {recall.recall_id} "
                f"on {details}. "
                f"Risk Class: {recall.risk_class or 'Not specified'}."
            )

            recommended_action = (
                f"POTENTIALLY AFFECTED: Review and follow the applicable "
                f"manufacturer/FDA recall instructions. "
                f"Inventory location: {item.location or 'Hospital Warehouse'}. "
                f"Source recall action: "
                f"'{recall.action or 'Refer to the applicable recall notice.'}'"
            )

        elif status == MatchStatus.NEEDS_REVIEW:
            reasons = []

            if "MANUFACTURER_MATCH" in signals:
                reasons.append(
                    "Manufacturer match confirmed"
                )
            elif "AI_MANUFACTURER_CANDIDATE" in signals:
                reasons.append(
                    "AI candidate manufacturer match"
                )

            if (
                "EXACT_MODEL_MATCH" in signals
                or "FUZZY_MODEL_MATCH" in signals
            ):
                reasons.append(
                    f"Model ({item.model or 'unspecified'}) "
                    f"resembles recalled scope"
                )
            elif "AI_MODEL_CANDIDATE" in signals:
                reasons.append(
                    f"AI candidate model match ({item.model or 'unspecified'})"
                )

            if (
                "EXACT_CATALOG_MATCH" in signals
                or "FUZZY_CATALOG_MATCH" in signals
            ):
                reasons.append(
                    f"Catalog number ({item.catalog_number or 'unspecified'}) "
                    f"matches product family"
                )
            elif "AI_CATALOG_CANDIDATE" in signals:
                reasons.append(
                    f"AI candidate catalog match ({item.catalog_number or 'unspecified'})"
                )

            if "PRODUCT_FAMILY_MATCH" in signals:
                reasons.append(
                    "Product family token overlap"
                )
            elif "AI_PRODUCT_FAMILY_CANDIDATE" in signals:
                reasons.append(
                    "AI candidate product family overlap"
                )


            evidence = (
                f"NEEDS REVIEW: Item {item.inventory_id} "
                f"({item.product_name}) shares key attributes with Recall "
                f"{recall.recall_id} ({'; '.join(reasons)}), but lot/serial "
                f"or catalog specificity requires manual verification."
            )

            recommended_action = (
                f"FLAGGED FOR MANUAL INSPECTION: Biomedical staff should "
                f"physically inspect unit at "
                f"{item.location or 'current department'} "
                f"and verify lot number "
                f"'{item.lot_number or 'N/A'}' / serial number "
                f"'{item.serial_number or 'N/A'}' against FDA recall scope."
            )

        else:  # NOT_AFFECTED
            evidence = (
                f"NOT AFFECTED: Item {item.inventory_id} "
                f"({item.product_name} by {item.manufacturer}) does not match "
                f"the manufacturer, model, or catalog specifications defined "
                f"in FDA Recall {recall.recall_id}."
            )

            recommended_action = (
                "No matching recall evidence found in the available inventory "
                "and recall identifiers. "
                "This result is a screening outcome, not a safety determination."
            )

        return evidence, recommended_action
