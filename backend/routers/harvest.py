"""Harvest protection & profit optimization routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.harvest import HarvestAnalyzeRequest, HarvestProtectionItemOut, HarvestProtectionSummaryOut
from services.harvest_protection_service import analyze_custom_crop_harvest, get_farmer_harvest_protection
from utils.security import get_current_farmer

router = APIRouter(prefix="/api/v1/harvest", tags=["Harvest Protection & Profit"])


@router.get("/protection", response_model=HarvestProtectionSummaryOut)
async def get_harvest_protection(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await get_farmer_harvest_protection(db, current_farmer)


@router.post("/analyze", response_model=HarvestProtectionItemOut)
async def analyze_crop_harvest(
    payload: HarvestAnalyzeRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
):
    return await analyze_custom_crop_harvest(current_farmer, payload)
