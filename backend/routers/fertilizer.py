"""Fertilizer recommendation router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.fertilizer import FertilizerRecommendationOut, FertilizerRequest
from services.fertilizer_service import generate_fertilizer_plan
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/fertilizer", tags=["Fertilizer"])


@router.post("/recommend", response_model=FertilizerRecommendationOut)
async def recommend_fertilizer(
    payload: FertilizerRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await generate_fertilizer_plan(db, current_farmer, payload)
