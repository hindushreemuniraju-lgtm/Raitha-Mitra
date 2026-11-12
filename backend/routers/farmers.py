"""Farmer profile endpoints including profile photo upload."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.auth import FarmerProfileOut, FarmerProfileUpdate
from services.farmer_service import (
    serialize_farmer_profile,
    update_farmer_profile,
    upload_farmer_photo,
)
from utils.rate_limit import rate_limit
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/farmers", tags=["Farmers"])


@router.get("/me", response_model=FarmerProfileOut)
def get_my_profile(current_farmer: Farmer = Depends(get_current_farmer)):
    return serialize_farmer_profile(current_farmer)


@router.put("/me", response_model=FarmerProfileOut)
def update_my_profile(
    payload: FarmerProfileUpdate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return update_farmer_profile(db, current_farmer, payload)


@router.post(
    "/me/photo",
    response_model=FarmerProfileOut,
    dependencies=[Depends(rate_limit(max_requests=15, window_seconds=60))],
)
async def upload_my_profile_photo(
    file: UploadFile = File(...),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await upload_farmer_photo(db, current_farmer, file)
