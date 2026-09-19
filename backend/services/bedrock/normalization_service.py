import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.models.schemas import InventoryItem
from backend.services.bedrock.bedrock_client import BedrockClient

logger = logging.getLogger("recallmatch.bedrock.normalization")


class BedrockNormalizationOutput(BaseModel):
    """Structured JSON schema returned by Bedrock for normalization assistance."""

    normalized_manufacturer: Optional[str] = Field(None, description="Standardized brand/manufacturer name")
    normalized_product_name: Optional[str] = Field(None, description="Clean product description without noise")
    normalized_model: Optional[str] = Field(None, description="Extracted standard model designation")
    normalized_catalog_number: Optional[str] = Field(None, description="Extracted standard reference or catalog number")
    candidate_identifiers: List[str] = Field(default_factory=list, description="Extracted alternate identifiers or codes")
    candidate_product_family: Optional[str] = Field(None, description="Extracted primary device family")
    reasoning_summary: str = Field("", description="Brief explanation of normalization mapping")


SYSTEM_PROMPT = """You are a specialized medical-device data normalization assistant.
Your task is ONLY to extract and standardize device attributes (manufacturer name, product name, model, catalog number, product family) from raw inventory records independently.

CRITICAL CONSTRAINTS:
1. Return ONLY a single valid JSON object adhering strictly to the JSON schema.
2. Do NOT invent identifiers, catalog numbers, or values that are not present or strongly derivable from the inventory record.
3. Do NOT evaluate if an item is recalled or affected.
4. Do NOT provide medical advice or clinical safety determinations.
5. Do NOT output match status or confirmation decisions.
"""


class BedrockNormalizationService:
    """Service to normalize messy inventory item variations using Amazon Bedrock."""

    def __init__(self, bedrock_client: Optional[BedrockClient] = None):
        self.bedrock_client = bedrock_client or BedrockClient()

    def normalize_item(
        self,
        item: InventoryItem,
    ) -> Optional[BedrockNormalizationOutput]:
        """
        Invokes Bedrock to normalize an inventory item independently.
        Returns BedrockNormalizationOutput or None on failure/missing credentials.
        """
        prompt = f"""Normalize the following hospital inventory item parameters into standardized attributes.

Raw Inventory Item:
- Manufacturer: {item.manufacturer}
- Product Name: {item.product_name}
- Model: {item.model or 'N/A'}
- Catalog Number: {item.catalog_number or 'N/A'}
- UDI-DI: {item.udi_di or 'N/A'}

Respond strictly with a JSON object matching this schema:
{{
  "normalized_manufacturer": "<standardized manufacturer name>",
  "normalized_product_name": "<clean product name>",
  "normalized_model": "<model designation or null>",
  "normalized_catalog_number": "<catalog ref number or null>",
  "candidate_identifiers": ["<identifier1>", "<identifier2>"],
  "candidate_product_family": "<product family or null>",
  "reasoning_summary": "<brief summary of normalization adjustments>"
}}
"""

        data = self.bedrock_client.invoke_structured(prompt, system_prompt=SYSTEM_PROMPT)
        if not data:
            return None

        try:
            return BedrockNormalizationOutput(
                normalized_manufacturer=data.get("normalized_manufacturer"),
                normalized_product_name=data.get("normalized_product_name"),
                normalized_model=data.get("normalized_model"),
                normalized_catalog_number=data.get("normalized_catalog_number"),
                candidate_identifiers=data.get("candidate_identifiers") or [],
                candidate_product_family=data.get("candidate_product_family"),
                reasoning_summary=data.get("reasoning_summary") or "",
            )
        except Exception as e:
            logger.warning(f"Failed to parse Bedrock JSON into BedrockNormalizationOutput: {e}")
            return None
