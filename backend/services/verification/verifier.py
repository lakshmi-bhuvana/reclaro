from typing import List, Optional
from backend.models.schemas import (
    InventoryItem,
    NormalizedRecall,
    MatchStatus,
)
from backend.services.matching.candidate_generator import SignalGenerator


class VerificationEngine:
    """
    Deterministic verification engine for Reclaro.

    The matching layer generates candidate signals.
    This layer is the authority that decides whether an item can be:

    - CONFIRMED
    - NEEDS_REVIEW
    - NOT_AFFECTED

    A CONFIRMED result requires deterministic evidence.
    Semantic/fuzzy/AI matching alone can never produce CONFIRMED.
    """

    @staticmethod
    def verify(
        item: InventoryItem,
        recall: NormalizedRecall,
        signals: Optional[List[str]] = None,
    ) -> MatchStatus:

        if signals is None:
            signals = SignalGenerator.evaluate_signals(item, recall)

        # ---------------------------------------------------------
        # Core deterministic signals
        # ---------------------------------------------------------

        mfr_matched = "MANUFACTURER_MATCH" in signals
        udi_matched = "EXACT_UDI_MATCH" in signals
        catalog_matched = "EXACT_CATALOG_MATCH" in signals
        model_matched = "EXACT_MODEL_MATCH" in signals

        lot_matched = "EXACT_LOT_MATCH" in signals
        serial_matched = "EXACT_SERIAL_MATCH" in signals

        # ---------------------------------------------------------
        # AI candidate signals
        # ---------------------------------------------------------

        ai_mfr_candidate = "AI_MANUFACTURER_CANDIDATE" in signals
        ai_model_candidate = "AI_MODEL_CANDIDATE" in signals
        ai_catalog_candidate = "AI_CATALOG_CANDIDATE" in signals
        ai_family_candidate = "AI_PRODUCT_FAMILY_CANDIDATE" in signals

        # ---------------------------------------------------------
        # Recall scope
        # ---------------------------------------------------------

        lot_scope_unrestricted = (
            not recall.lot_ranges
            or "ALL_LOTS" in recall.lot_ranges
        )

        serial_scope_unrestricted = (
            not recall.serial_ranges
            or "ALL_SERIALS" in recall.serial_ranges
        )

        lot_scope_satisfied = (
            lot_matched or lot_scope_unrestricted
        )

        serial_scope_satisfied = (
            serial_matched or serial_scope_unrestricted
        )

        distribution_scope_satisfied = True

        if recall.distribution_date_before is not None:
            distribution_scope_satisfied = (
                item.distribution_date is not None
                and item.distribution_date < recall.distribution_date_before
            )

        # ---------------------------------------------------------
        # Fuzzy / semantic candidate signals
        # ---------------------------------------------------------

        fuzzy_model = "FUZZY_MODEL_MATCH" in signals
        fuzzy_catalog = "FUZZY_CATALOG_MATCH" in signals
        family_matched = "PRODUCT_FAMILY_MATCH" in signals

        # ---------------------------------------------------------
        # Rule 1: CONFIRMED
        #
        # Deterministic Manufacturer must match.
        # Deterministic identifier (exact UDI, exact catalog, exact model)
        # must match.
        # Lot/serial/distribution scope must be satisfied.
        #
        # AI candidate signals alone or combined can NEVER produce CONFIRMED.
        # ---------------------------------------------------------

        if mfr_matched:

            scope_satisfied = (
                lot_scope_satisfied
                and serial_scope_satisfied
                and distribution_scope_satisfied
            )

            if scope_satisfied:

                # Exact UDI-DI match
                if udi_matched:
                    return MatchStatus.CONFIRMED

                # Exact catalog number match
                if catalog_matched:
                    return MatchStatus.CONFIRMED

                # Exact model match
                if model_matched:
                    return MatchStatus.CONFIRMED

        # ---------------------------------------------------------
        # Rule 2: NEEDS_REVIEW
        #
        # There is meaningful evidence (deterministic, fuzzy, or AI candidate)
        # that the inventory item may belong to the recall, but deterministic
        # proof is incomplete or lot/serial restriction remains unverified.
        # ---------------------------------------------------------

        any_mfr_candidate = mfr_matched or ai_mfr_candidate
        any_model_candidate = model_matched or fuzzy_model or ai_model_candidate
        any_catalog_candidate = catalog_matched or fuzzy_catalog or ai_catalog_candidate
        any_family_candidate = family_matched or ai_family_candidate
        any_udi_candidate = udi_matched

        if any_mfr_candidate and (
            any_udi_candidate
            or any_model_candidate
            or any_catalog_candidate
            or any_family_candidate
        ):
            return MatchStatus.NEEDS_REVIEW

        # ---------------------------------------------------------
        # Rule 3: NOT_AFFECTED
        # ---------------------------------------------------------

        return MatchStatus.NOT_AFFECTED