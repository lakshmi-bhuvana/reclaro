
from typing import List, Set, Optional
from backend.models.schemas import InventoryItem, NormalizedRecall
from backend.services.normalization.normalizer import TextNormalizer


class SignalGenerator:
    """Generates deterministic and candidate matching signals for an inventory item against a recall."""

    @staticmethod
    def evaluate_signals(
        item: InventoryItem,
        recall: NormalizedRecall,
        ai_signals: Optional[List[str]] = None,
    ) -> List[str]:
        signals: List[str] = []


        item_mfr = TextNormalizer.normalize_manufacturer(item.manufacturer)
        recall_mfr = TextNormalizer.normalize_manufacturer(recall.manufacturer)

        # 1. Manufacturer Match
        mfr_match = False
        if item_mfr and recall_mfr:
            if item_mfr in recall_mfr or recall_mfr in item_mfr:
                mfr_match = True
                signals.append("MANUFACTURER_MATCH")
            else:
                item_tokens = TextNormalizer.extract_tokens(item_mfr)
                recall_tokens = TextNormalizer.extract_tokens(recall_mfr)
                if item_tokens and recall_tokens and (item_tokens & recall_tokens):
                    mfr_match = True
                    signals.append("MANUFACTURER_MATCH")

        # 2. UDI DI Match
        if item.udi_di and recall.udi_di:
            item_udi = TextNormalizer.normalize_code(item.udi_di)
            for r_udi in recall.udi_di:
                if item_udi == TextNormalizer.normalize_code(r_udi):
                    signals.append("EXACT_UDI_MATCH")
                    break

        # 3. Catalog Number Match
        item_cat = TextNormalizer.normalize_code(item.catalog_number)
        if item_cat and recall.catalog_numbers:
            for r_cat in recall.catalog_numbers:
                norm_r_cat = TextNormalizer.normalize_code(r_cat)
                if item_cat == norm_r_cat:
                    signals.append("EXACT_CATALOG_MATCH")
                    break
                elif len(item_cat) >= 4 and (
                    item_cat in norm_r_cat or norm_r_cat in item_cat
                ):
                    signals.append("FUZZY_CATALOG_MATCH")
                    break

        # 4. Model Match
        item_model = item.model.upper().strip() if item.model else ""
        if item_model and recall.models:
            for r_model in recall.models:
                norm_r_model = r_model.upper().strip()
                if (
                    item_model == norm_r_model
                    or TextNormalizer.normalize_code(item_model)
                    == TextNormalizer.normalize_code(norm_r_model)
                ):
                    signals.append("EXACT_MODEL_MATCH")
                    break
                elif len(item_model) >= 3 and (
                    item_model in norm_r_model or norm_r_model in item_model
                ):
                    signals.append("FUZZY_MODEL_MATCH")
                    break

        # 5. Lot Match
        item_lot = TextNormalizer.normalize_code(item.lot_number)

        if item_lot and recall.lot_ranges:
            # ALL_LOTS is recall scope, not an item-level match.
            # Do NOT emit it as a matching signal.
            if "ALL_LOTS" not in recall.lot_ranges:
                for r_lot in recall.lot_ranges:
                    if item_lot == TextNormalizer.normalize_code(r_lot):
                        signals.append("EXACT_LOT_MATCH")
                        break

        item_sn = TextNormalizer.normalize_code(item.serial_number)

        if item_sn and recall.serial_ranges:
            # ALL_SERIALS is recall scope, not an item-level match.
            # Do NOT emit it as a matching signal.
            if "ALL_SERIALS" not in recall.serial_ranges:
                for r_sn in recall.serial_ranges:
                    if item_sn == TextNormalizer.normalize_code(r_sn):
                        signals.append("EXACT_SERIAL_MATCH")
                        break

        # 6. Serial Match
        item_sn = TextNormalizer.normalize_code(item.serial_number)

        if item_sn and recall.serial_ranges:
            if "ALL_SERIALS" in recall.serial_ranges:
                signals.append("SERIAL_MATCH_ALL")
            else:
                for r_sn in recall.serial_ranges:
                    if item_sn == TextNormalizer.normalize_code(r_sn):
                        signals.append("EXACT_SERIAL_MATCH")
                        break

        # 7. Product Family / Token Overlap
        item_title_tokens = TextNormalizer.extract_tokens(item.product_name)

        if item_title_tokens:
            for family in recall.product_families:
                family_tokens = TextNormalizer.extract_tokens(family)
                if family_tokens and family_tokens.issubset(item_title_tokens):
                    signals.append("PRODUCT_FAMILY_MATCH")
                    break

        if ai_signals:
            for s in ai_signals:
                if s not in signals:
                    signals.append(s)

        return signals
