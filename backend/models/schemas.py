from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

class MatchStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NOT_AFFECTED = "NOT_AFFECTED"


class Recall(BaseModel):
    """Raw FDA Recall item schema directly mapping openFDA response"""

    recall_id: str = Field(..., description="Unique openFDA Recall Event ID or Number")
    recalling_firm: str = Field(..., description="Firm issuing the recall")
    product_description: str = Field(..., description="Full description of the recalled device")
    product_code: Optional[str] = Field(None, description="FDA product code classification")
    reason_for_recall: Optional[str] = Field(None, description="Detailed reason for recall issuance")
    action: Optional[str] = Field(None, description="Action requested by FDA/Firm")
    classification: Optional[str] = Field(None, description="FDA Risk Classification (Class I, II, III)")
    event_date_initiated: Optional[str] = Field(None, description="Recall initiation date (YYYYMMDD or formatted)")
    code_info: Optional[str] = Field(None, description="Lot numbers, serial numbers, catalog numbers, UDI DI info")
    source_url: Optional[str] = Field(None, description="Direct URL to openFDA record or official notice")


class NormalizedRecall(BaseModel):
    """Normalized structured recall scope extracted from raw recall notice"""

    recall_id: str
    manufacturer: str
    product_families: List[str] = Field(default_factory=list)
    models: List[str] = Field(default_factory=list)
    catalog_numbers: List[str] = Field(default_factory=list)
    udi_di: List[str] = Field(default_factory=list)
    lot_ranges: List[str] = Field(default_factory=list)
    serial_ranges: List[str] = Field(default_factory=list)

    # Conditional distribution scope, when stated by FDA.
    # Example: "All Serial Numbers distributed prior to 07/09/2018"
    distribution_date_before: Optional[date] = None

    action: Optional[str] = None
    risk_class: Optional[str] = None


class InventoryItem(BaseModel):
    """Hospital inventory item parsed from CSV upload"""

    inventory_id: str = Field(..., description="Hospital unique inventory tracking identifier")
    manufacturer: str = Field(..., description="Device manufacturer name")
    product_name: str = Field(..., description="Commercial or trade name of the product")
    model: Optional[str] = Field(None, description="Model number or designation")
    catalog_number: Optional[str] = Field(None, description="Catalog or reference number (REF)")
    udi_di: Optional[str] = Field(None, description="Unique Device Identifier - Device Identifier component")
    lot_number: Optional[str] = Field(None, description="Batch or lot number")
    serial_number: Optional[str] = Field(None, description="Individual unit serial number")

    distribution_date: Optional[date] = Field(
        None,
        description="Date the inventory item was distributed or supplied",
    )

    quantity: Optional[int] = Field(1, description="Quantity in stock")
    location: Optional[str] = Field(None, description="Physical hospital location or department")

class MatchResult(BaseModel):
    """Outcome of matching an InventoryItem against a NormalizedRecall"""

    inventory_id: str
    recall_id: str
    status: MatchStatus
    signals: List[str] = Field(default_factory=list, description="Rule signals triggered during evaluation")
    evidence: str = Field(..., description="Concise human-readable evidence explaining classification")
    recommended_action: str = Field(..., description="Operational action for biomedical engineering/clinical staff")


class RecallSearchResponse(BaseModel):
    """API response contract for listing recalls"""

    total: int
    recalls: List[Recall]


class MatchResponse(BaseModel):
    """API response contract for inventory recall verification audit"""

    run_id: Optional[str] = None
    recall: Recall
    normalized_recall: NormalizedRecall
    total_audited: int
    confirmed_count: int
    needs_review_count: int
    not_affected_count: int
    inventory_storage_key: Optional[str] = None
    results: List[MatchResult]
