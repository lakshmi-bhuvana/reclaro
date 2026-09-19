import csv
import io
import logging
from typing import List, Optional
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import (
    Recall,
    NormalizedRecall,
    InventoryItem,
    MatchResult,
    MatchStatus,
    MatchResponse,
    RecallSearchResponse,
)
from backend.services.fda.fda_client import OpenFDAClient
from backend.services.recall_parser.parser import RecallParser
from backend.services.evidence.evidence_builder import EvidenceBuilder
from backend.services.bedrock.candidate_service import BedrockCandidateService
from backend.services.storage.s3_storage import S3StorageService

logger = logging.getLogger("recallmatch")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="RecallMatch API",
    description="Medical Device FDA Recall Identification and Inventory Matching Platform",
    version="1.0.0",
)

# Enable CORS for local React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fda_client = OpenFDAClient()
bedrock_candidate_service = BedrockCandidateService()
s3_storage_service = S3StorageService()




@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "RecallMatch Engine", "version": "1.0.0"}


@app.get("/api/recalls", response_model=RecallSearchResponse)
async def list_recalls(
    limit: int = Query(20, ge=1, le=50),
    search: Optional[str] = Query(None, description="Search query for firm or product description"),
):
    """Fetch live or cached openFDA medical device recall events."""
    recalls = await fda_client.fetch_recalls(limit=limit, search=search)
    return RecallSearchResponse(total=len(recalls), recalls=recalls)


@app.get("/api/recalls/{recall_id}")
async def get_recall_detail(recall_id: str):
    """Fetch detail and normalized scope for a specific FDA recall ID."""
    recall = await fda_client.get_recall_by_id(recall_id)
    if not recall:
        raise HTTPException(status_code=404, detail=f"Recall with ID '{recall_id}' not found.")

    normalized = RecallParser.parse(recall)
    return {"recall": recall, "normalized_recall": normalized}


@app.post("/api/match", response_model=MatchResponse)
async def match_inventory(
    recall_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload hospital inventory CSV file and audit against selected FDA Recall."""
    # 1. Fetch target recall
    recall = await fda_client.get_recall_by_id(recall_id)
    if not recall:
        raise HTTPException(status_code=404, detail=f"Recall ID '{recall_id}' not found.")

    normalized_recall = RecallParser.parse(recall)

    # 2. Read uploaded CSV file and persist to S3 storage
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV file upload: {str(e)}")

    try:
        inventory_storage_key = s3_storage_service.upload_inventory_csv(
            contents=contents,
            filename=file.filename or "inventory.csv",
        )
    except Exception as e:
        logger.error(f"S3 inventory storage failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Inventory storage service is unavailable: {str(e)}",
        )

    # 3. Parse CSV file
    try:
        text_content = contents.decode("utf-8-sig")
        csv_reader = csv.DictReader(io.StringIO(text_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV file format: {str(e)}")

    inventory_items: List[InventoryItem] = []
    row_idx = 1
    for row in csv_reader:
        # Standardize key access regardless of minor case variations
        clean_row = {
            k.strip().lower(): (v.strip() if v is not None else "")
            for k, v in row.items()
            if k
        }
        inv_id = clean_row.get("inventory_id") or clean_row.get("id") or f"INV-{row_idx:04d}"
        mfr = clean_row.get("manufacturer") or clean_row.get("mfr") or clean_row.get("vendor") or "Unknown"
        pname = clean_row.get("product_name") or clean_row.get("product") or clean_row.get("description") or "Unknown Device"

        try:
            qty = int(clean_row.get("quantity") or 1)
        except ValueError:
            qty = 1

        item = InventoryItem(
            inventory_id=inv_id,
            manufacturer=mfr,
            product_name=pname,
            model=clean_row.get("model"),
            catalog_number=clean_row.get("catalog_number") or clean_row.get("ref"),
            udi_di=clean_row.get("udi_di") or clean_row.get("udi"),
            lot_number=clean_row.get("lot_number") or clean_row.get("lot"),
            serial_number=clean_row.get("serial_number") or clean_row.get("serial") or clean_row.get("sn"),
            quantity=qty,
            location=clean_row.get("location") or clean_row.get("department"),
        )
        inventory_items.append(item)
        row_idx += 1

    if not inventory_items:
        raise HTTPException(status_code=400, detail="Uploaded CSV contained no valid inventory rows.")

    # 4. Evaluate each item through deterministic verification engine
    results: List[MatchResult] = []
    confirmed_cnt = 0
    needs_review_cnt = 0
    not_affected_cnt = 0

    for item in inventory_items:
        ai_signals = None
        try:
            ai_signals = bedrock_candidate_service.generate_candidate_signals(item, normalized_recall)
        except Exception as e:
            logger.warning(f"Bedrock candidate generation failed for item {item.inventory_id}: {e}")

        match_res = EvidenceBuilder.build_match_result(item, normalized_recall, ai_signals=ai_signals)
        results.append(match_res)

        if match_res.status == MatchStatus.CONFIRMED:
            confirmed_cnt += 1
        elif match_res.status == MatchStatus.NEEDS_REVIEW:
            needs_review_cnt += 1
        else:
            not_affected_cnt += 1

    return MatchResponse(
        recall=recall,
        normalized_recall=normalized_recall,
        total_audited=len(inventory_items),
        confirmed_count=confirmed_cnt,
        needs_review_count=needs_review_cnt,
        not_affected_count=not_affected_cnt,
        inventory_storage_key=inventory_storage_key,
        results=results,
    )
