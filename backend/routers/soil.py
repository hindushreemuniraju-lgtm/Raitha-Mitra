"""Soil health router (lab upload + OCR + mandatory review + dataset estimate)."""

from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.soil import (
    SoilEstimateRequest,
    SoilRecordOut,
    SoilRecordReviewRequest,
    SoilUploadExtractionOut,
)
from services.soil_service import (
    create_dataset_soil_estimate,
    list_farmer_soil_records,
    review_and_confirm_soil_record,
    upload_and_extract_soil_report,
)
from utils.rate_limit import rate_limit
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/soil", tags=["Soil Health"])


@router.get("/records", response_model=List[SoilRecordOut])
def get_my_soil_records(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_farmer_soil_records(db, current_farmer.id)


@router.post(
    "/upload",
    response_model=SoilUploadExtractionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
async def upload_soil_report(
    file: UploadFile = File(...),
    source_type: str = Form(default="soil_health_card"),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    record, ocr_status, ocr_note = await upload_and_extract_soil_report(
        db, current_farmer, file, source_type
    )
    return SoilUploadExtractionOut(
        record=record,
        ocr_status=ocr_status,
        ocr_note=ocr_note,
        requires_review=True,
    )


@router.put("/records/{record_id}/review", response_model=SoilRecordOut)
def confirm_soil_review(
    record_id: int,
    payload: SoilRecordReviewRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return review_and_confirm_soil_record(db, current_farmer, record_id, payload)


@router.post("/estimate", response_model=SoilRecordOut, status_code=status.HTTP_201_CREATED)
def estimate_soil_by_gps(
    payload: SoilEstimateRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return create_dataset_soil_estimate(
        db,
        current_farmer,
        payload.latitude,
        payload.longitude,
        payload.dataset_preference,
    )
