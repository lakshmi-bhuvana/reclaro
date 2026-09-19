import re
from typing import List

from backend.models.schemas import Recall, NormalizedRecall
from backend.services.normalization.normalizer import TextNormalizer


class RecallParser:
    """Parses raw openFDA Recall objects and extracts structured search scope parameters."""

    @staticmethod
    def parse(recall: Recall) -> NormalizedRecall:
        manufacturer = TextNormalizer.normalize_manufacturer(
            recall.recalling_firm
        )

        combined_text = (
            f"{recall.product_description or ''} "
            f"{recall.code_info or ''}"
        )

        # Extract catalog / reference numbers
        catalog_numbers = RecallParser._extract_catalog_numbers(
            combined_text
        )

        # Extract models
        models = RecallParser._extract_models(combined_text)

        # Extract UDI-DI
        udi_di = RecallParser._extract_udi_di(combined_text)

        # Extract lot / serial ranges
        lot_ranges = RecallParser._extract_lots(
            recall.code_info or ""
        )

        serial_ranges = RecallParser._extract_serials(
            recall.code_info or ""
        )

        # Extract product family keywords / names
        product_families = RecallParser._extract_product_families(
            recall.product_description or ""
        )

        return NormalizedRecall(
            recall_id=recall.recall_id,
            manufacturer=manufacturer,
            product_families=product_families,
            models=models,
            catalog_numbers=catalog_numbers,
            udi_di=udi_di,
            lot_ranges=lot_ranges,
            serial_ranges=serial_ranges,
            action=recall.action,
            risk_class=recall.classification or "Class II",
        )

    @staticmethod
    def _extract_catalog_numbers(text: str) -> List[str]:
        catalogs = set()

        # ---------------------------------------------------------
        # 1. Explicit catalog/reference/part number patterns
        #
        # Examples:
        #   REF: HV-100-REF
        #   Catalog # 99577-000001
        #   Part Number 8100-0003
        #   Reorder 74021210
        # ---------------------------------------------------------
        ref_pattern = (
            r"(?:ref(?:erence)?|catalog(?:ue)?(?:\s+number|\s+#)?|"
            r"cat(?:alog)?\s*#|part(?:\s+number)?|reorder)"
            r"\s*[\#\:\.\-]?\s*"
            r"([a-zA-Z0-9\-\/]{4,20})"
        )

        matches = re.findall(
            ref_pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            clean_code = TextNormalizer.normalize_code(match)

            if (
                len(clean_code) >= 4
                and any(ch.isdigit() for ch in clean_code)
            ):
                catalogs.add(clean_code)

        # ---------------------------------------------------------
        # 2. Explicit "Catalog Numbers:" lists
        #
        # Example:
        #   Catalog Numbers:
        #   74021210, 74021211, ... 74021229
        #
        # Only extract identifiers from catalog-number context.
        # ---------------------------------------------------------
        catalog_list_patterns = [
            r"catalog\s+numbers?\s*[:#]\s*([^.;\n]+)",
            r"catalog\s+nos?\.?\s*[:#]\s*([^.;\n]+)",
            r"catalog\s*#\s*([^.;\n]+)",
            r"cat(?:alog)?\s+numbers?\s*[:#]\s*([^.;\n]+)",
        ]

        for pattern in catalog_list_patterns:
            list_matches = re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )

            for catalog_text in list_matches:
                parts = re.split(r"[,;]", catalog_text)

                for part in parts:
                    part = re.sub(
                        r"^\s*(?:and|or)\s+",
                        "",
                        part,
                        flags=re.IGNORECASE,
                    ).strip()

                    identifier_matches = re.findall(
                        r"\b(?:[A-Za-z]{1,6}[-/]?)?"
                        r"[0-9][A-Za-z0-9]*"
                        r"(?:[-/][A-Za-z0-9]+)*\b",
                        part,
                    )

                    for identifier in identifier_matches:
                        clean_code = TextNormalizer.normalize_code(
                            identifier
                        )

                        if (
                            len(clean_code) >= 4
                            and any(ch.isdigit() for ch in clean_code)
                        ):
                            catalogs.add(clean_code)

        # ---------------------------------------------------------
        # 3. Existing structured catalog formats
        #
        # Examples:
        #   ABC-123-XYZ
        #   99577-000001
        # ---------------------------------------------------------
        structured_patterns = [
            r"\b([a-zA-Z]{1,3}\-[0-9]{3,6}\-[a-zA-Z0-9]{2,6})\b",
            r"\b([0-9]{5}\-[0-9]{6})\b",
        ]

        for pattern in structured_patterns:
            matches = re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )

            for match in matches:
                clean_code = TextNormalizer.normalize_code(match)

                if (
                    len(clean_code) >= 4
                    and any(ch.isdigit() for ch in clean_code)
                ):
                    catalogs.add(clean_code)

        # ---------------------------------------------------------
        # 4. Numeric catalog ranges
        #
        # Examples:
        #   74021210 through 74021229
        #   74021210 thru 74021229
        #   74021210 to 74021229
        #
        # Expand only reasonably sized ranges.
        # ---------------------------------------------------------
        range_pattern = (
            r"\b(\d{6,12})\s+"
            r"(?:through|thru|to)\s+"
            r"(\d{6,12})\b"
        )

        range_matches = re.findall(
            range_pattern,
            text,
            re.IGNORECASE,
        )

        for start, end in range_matches:
            start_num = int(start)
            end_num = int(end)

            # Safety limit prevents accidental huge expansions.
            if (
                end_num >= start_num
                and (end_num - start_num) <= 1000
            ):
                for number in range(start_num, end_num + 1):
                    catalogs.add(str(number))

        return sorted(list(catalogs))

    @staticmethod
    def _extract_models(text: str) -> List[str]:
        models = set()

        # Examples:
        # Model HVAD-100
        # Model 775
        # Model CS300
        # SPEC-IQ-200
        # HeartMate 3
        # LIFEPAK 15
        model_patterns = [
            r"model\s*[\#\:\.\-]?\s*"
            r"([a-zA-Z0-9\-\/]{2,15})",

            r"\b(hvad-[a-zA-Z0-9\-]+)\b",

            r"\b(cs300-[a-zA-Z0-9\-]*)\b",

            r"\b(lifepak\s*\d+)\b",

            r"\b(heartmate\s*\d+)\b",

            r"\b(alaris\s*\d+)\b",

            r"\b(spectrum\s*iq)\b",
        ]

        for pattern in model_patterns:
            matches = re.findall(
                pattern,
                text,
                re.IGNORECASE,
            )

            for match in matches:
                models.add(match.strip().upper())

        return sorted(models)

    @staticmethod
    def _extract_udi_di(text: str) -> List[str]:
        udi_set = set()

        # GTIN-14 / UDI-DI:
        # 00 + 12 digits
        matches = re.findall(
            r"\b(00\d{12})\b",
            text,
        )

        for match in matches:
            udi_set.add(match)

        return sorted(udi_set)

    @staticmethod
    def _extract_lots(code_info: str) -> List[str]:
        lots = set()

        if not code_info:
            return []

        # Look for LOT / BATCH numbers
        matches = re.findall(
            r"(?:lot|batch)"
            r"\s*[\#\:\.\-]?\s*"
            r"([a-zA-Z0-9\-\_]+)",
            code_info,
            re.IGNORECASE,
        )

        for match in matches:
            clean_code = TextNormalizer.normalize_code(match)

            if len(clean_code) >= 3:
                lots.add(clean_code)

        # Capture all-lot recalls
        code_info_lower = code_info.lower()

        if (
            "all lots" in code_info_lower
            or "all affected" in code_info_lower
        ):
            lots.add("ALL_LOTS")

        return sorted(lots)

    @staticmethod
    def _extract_serials(code_info: str) -> List[str]:
        serials = set()

        if not code_info:
            return []

        # Look for serial numbers
        matches = re.findall(
            r"(?:sn|serial|s/n)"
            r"\s*[\#\:\.\-]?\s*"
            r"([a-zA-Z0-9\-\_]+)",
            code_info,
            re.IGNORECASE,
        )

        for match in matches:
            clean_code = TextNormalizer.normalize_code(match)

            if len(clean_code) >= 3:
                serials.add(clean_code)

        # Capture all-serial recalls
        if "all serial" in code_info.lower():
            serials.add("ALL_SERIALS")

        return sorted(serials)

    @staticmethod
    def _extract_product_families(desc: str) -> List[str]:
        """
        Extract product-family names from the FDA product description.

        The parser uses two complementary approaches:

        1. Known generic medical-device families such as
           "infusion pump", "catheter", "defibrillator", etc.

        2. The primary named product phrase at the beginning of the
           FDA description.

        The second approach is important for recalls such as:

            "Journey BCS Knee CoCr Femoral Components,
             Catalog Numbers: ..."

        which should produce a family such as:

            "Journey BCS Knee CoCr Femoral Component"

        rather than relying on a hardcoded keyword list.
        """

        families = set()

        if not desc:
            return []

        desc_clean = " ".join(desc.split())
        desc_lower = desc_clean.lower()

        # ---------------------------------------------------------
        # 1. Known generic medical-device families
        # ---------------------------------------------------------
        keywords = [
            "infusion pump",
            "ventricular assist",
            "defibrillator",
            "pacemaker",
            "catheter",
            "ventilator",
            "warming unit",
            "monitor",
            "balloon pump",
            "stent",
            "valve",
        ]

        for keyword in keywords:
            if keyword in desc_lower:
                families.add(keyword.title())

        # ---------------------------------------------------------
        # 2. Extract the primary named product phrase.
        #
        # FDA descriptions commonly start like:
        #
        #   Journey BCS Knee CoCr Femoral Components,
        #   Catalog Numbers: ...
        #
        #   Penumbra Neuron Delivery Catheter 070,
        #   percutaneous catheter, catalog numbers ...
        #
        #   MiniMed 630G Insulin Pump, REF: ...
        #
        # We take the first meaningful clause before a comma/semicolon.
        # ---------------------------------------------------------
        primary_clause = re.split(
            r"[,;]",
            desc_clean,
            maxsplit=1,
        )[0].strip()

        if primary_clause:
            # Remove common introductory labels.
            primary_clause = re.sub(
                r"^(?:product|device|model|description)\s*[:\-]\s*",
                "",
                primary_clause,
                flags=re.IGNORECASE,
            ).strip()

            # Remove trailing punctuation.
            primary_clause = primary_clause.strip(" .:-")

            # Avoid adding extremely long prose as a product family.
            words = primary_clause.split()

            if 2 <= len(words) <= 15:
                # Remove obvious non-product prefixes.
                ignored_prefixes = {
                    "the",
                    "a",
                    "an",
                }

                while (
                    words
                    and words[0].lower() in ignored_prefixes
                ):
                    words.pop(0)

                if len(words) >= 2:
                    primary_clause = " ".join(words)

                    # Normalize plural "Components" -> "Component"
                    # so it can match inventory text such as
                    # "Femoral Component".
                    primary_clause = re.sub(
                        r"\bcomponents\b",
                        "component",
                        primary_clause,
                        flags=re.IGNORECASE,
                    )

                    # Normalize a few other common plural forms.
                    primary_clause = re.sub(
                        r"\bpumps\b",
                        "pump",
                        primary_clause,
                        flags=re.IGNORECASE,
                    )

                    primary_clause = re.sub(
                        r"\bcatheters\b",
                        "catheter",
                        primary_clause,
                        flags=re.IGNORECASE,
                    )

                    primary_clause = re.sub(
                        r"\bdevices\b",
                        "device",
                        primary_clause,
                        flags=re.IGNORECASE,
                    )

                    primary_clause = re.sub(
                        r"\bsystems\b",
                        "system",
                        primary_clause,
                        flags=re.IGNORECASE,
                    )

                    families.add(primary_clause)

        return sorted(families)