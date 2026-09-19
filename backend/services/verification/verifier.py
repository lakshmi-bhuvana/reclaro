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
    Semantic/fuzzy matching alone can never produce CONFIRMED.
    """

    @staticmethod
    def verify(
        item: InventoryItem,
        recall: NormalizedRecall,
    ) -> MatchStatus:

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
        # Recall scope
        #
        # If a recall does not specify a lot/serial restriction,
        # that dimension is considered unrestricted.
        #
        # If a restriction exists, the corresponding deterministic
        # match must be present before confirmation.
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

        # ---------------------------------------------------------
        # Fuzzy / semantic candidate signals
        #
        # These can identify candidates but can NEVER independently
        # produce CONFIRMED.
        # ---------------------------------------------------------

        fuzzy_model = "FUZZY_MODEL_MATCH" in signals
        fuzzy_catalog = "FUZZY_CATALOG_MATCH" in signals
        family_matched = "PRODUCT_FAMILY_MATCH" in signals

        # ---------------------------------------------------------
        # Rule 1: CONFIRMED
        #
        # Manufacturer must match.
        #
        # Then a deterministic identifier must match:
        #
        #   - exact UDI
        #   - exact catalog number
        #   - exact model
        #
        # AND every applicable lot/serial restriction must be
        # satisfied.
        #
        # This prevents an exact device-family match from being
        # incorrectly confirmed when the recall is restricted to
        # specific lots or serial numbers.
        # ---------------------------------------------------------

        if mfr_matched:

            scope_satisfied = (
                lot_scope_satisfied
                and serial_scope_satisfied
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
        # There is meaningful evidence that the inventory item may
        # belong to the recall, but deterministic proof is
        # incomplete.
        #
        # Examples:
        #   - manufacturer + product family
        #   - manufacturer + model but restricted lot unknown
        #   - manufacturer + catalog candidate
        #   - fuzzy model/catalog match
        #
        # These must not become CONFIRMED.
        # ---------------------------------------------------------

        if mfr_matched and (
            model_matched
            or catalog_matched
            or fuzzy_model
            or fuzzy_catalog
            or family_matched
        ):
            return MatchStatus.NEEDS_REVIEW

        # ---------------------------------------------------------
        # Rule 3: NOT_AFFECTED
        #
        # Available evidence does not establish that the inventory
        # item belongs to the selected recall scope.
        #
        # This is a screening result, not a medical/safety
        # determination.
        # ---------------------------------------------------------

        return MatchStatus.NOT_AFFECTED