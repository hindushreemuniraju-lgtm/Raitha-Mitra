"""Pest and disease detection router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.disease import DiseaseScanOut
from services.disease_service import analyze_crop_disease_image, list_disease_scans
from utils.rate_limit import rate_limit
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/pests", tags=["Pest & Disease"])


@router.get("/scans", response_model=List[DiseaseScanOut])
def get_my_scans(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_disease_scans(db, current_farmer.id)


@router.post(
    "/analyze",
    response_model=DiseaseScanOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))],
)
async def analyze_leaf_photo(
    file: UploadFile = File(...),
    crop_name: Optional[str] = Form(default=None),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await analyze_crop_disease_image(db, current_farmer, file, crop_name)
