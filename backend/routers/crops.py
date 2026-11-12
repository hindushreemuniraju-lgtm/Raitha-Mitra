"""Crop recommendation and growth stage monitoring router."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.crops import (
    CropRecommendRequest,
    CropRecommendResponse,
    TrackedCropCreate,
    TrackedCropOut,
    TrackedCropUpdate,
)
from services.crop_service import (
    create_tracked_crop,
    delete_tracked_crop,
    list_tracked_crops,
    recommend_crops_for_farmer,
    update_tracked_crop,
)
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/crops", tags=["Crops"])


@router.post("/recommend", response_model=CropRecommendResponse)
def recommend_crops(
    payload: CropRecommendRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return recommend_crops_for_farmer(db, current_farmer, payload)


@router.get("/monitoring", response_model=List[TrackedCropOut])
def get_monitoring_crops(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_tracked_crops(db, current_farmer.id)


@router.post("/monitoring", response_model=TrackedCropOut, status_code=status.HTTP_201_CREATED)
def add_monitoring_crop(
    payload: TrackedCropCreate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return create_tracked_crop(db, current_farmer, payload)


@router.put("/monitoring/{crop_id}", response_model=TrackedCropOut)
def edit_monitoring_crop(
    crop_id: int,
    payload: TrackedCropUpdate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return update_tracked_crop(db, current_farmer.id, crop_id, payload)


@router.delete("/monitoring/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_monitoring_crop(
    crop_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    delete_tracked_crop(db, current_farmer.id, crop_id)
