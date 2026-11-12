"""Farmer profile endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.auth import FarmerProfileOut, FarmerProfileUpdate
from services.farmer_service import update_farmer_profile
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/farmers", tags=["Farmers"])


@router.get("/me", response_model=FarmerProfileOut)
def get_my_profile(current_farmer: Farmer = Depends(get_current_farmer)):
    return current_farmer


@router.put("/me", response_model=FarmerProfileOut)
def update_my_profile(
    payload: FarmerProfileUpdate,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return update_farmer_profile(db, current_farmer, payload)
