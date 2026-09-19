import re
from typing import Set


class TextNormalizer:
    """Normalizes identifiers, manufacturer names, catalog numbers, and lot/serial numbers for precise matching."""

    @staticmethod
    def normalize_string(text: str | None) -> str:
        """Lowercases, strips leading/trailing whitespace, and removes non-alphanumeric punctuation."""
        if not text:
            return ""
        # Keep letters, numbers, and space/hyphen for structure
        cleaned = re.sub(r"[^\w\s\-]", "", text.lower())
        return " ".join(cleaned.split())

    @staticmethod
    def normalize_code(code: str | None) -> str:
        """Removes spaces, hyphens, and non-alphanumeric characters for raw code comparisons."""
        if not code:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", code.upper())

    @staticmethod
    def normalize_manufacturer(name: str | None) -> str:
        """Strips legal entity suffixes like Inc., Corp, LLC, Co., Ltd., and normalizes brand variations."""
        if not name:
            return ""
        norm = name.lower()
        suffixes = [
            r"\binc(orporated)?\b",
            r"\bcorp(oration)?\b",
            r"\bllc\b",
            r"\bltd\b",
            r"\bco(mpany)?\b",
            r"\bhealthcare\b",
            r"\bmedical\b",
            r"\bsystems?\b",
            r"\btechnologies\b",
            r"\bgroup\b",
            r"\bna\b",
            r"\busa\b",
        ]
        for s in suffixes:
            norm = re.sub(s, "", norm)

        norm = re.sub(r"[^\w\s]", "", norm)
        return " ".join(norm.split())

    @staticmethod
    def extract_tokens(text: str | None) -> Set[str]:
        """Extracts unique lowercase alphanumeric tokens longer than 2 characters."""
        if not text:
            return set()
        tokens = re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())
        # Filter out common stop words
        stop_words = {"the", "and", "for", "with", "system", "device", "model", "unit", "part", "ref", "cat", "lot", "sn", "pump"}
        return set(tokens) - stop_words
