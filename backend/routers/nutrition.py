"""Nutrition and crop utilization router."""

from fastapi import APIRouter, Depends, Query

from models.farmer import Farmer
from schemas.nutrition import NutritionQueryOut
from services.nutrition_service import query_nutrition_and_utilization
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/nutrition", tags=["Nutrition & Utilization"])


@router.get("", response_model=NutritionQueryOut)
async def get_nutrition_info(
    query: str = Query(default="ragi", min_length=2, max_length=100),
    _current_farmer: Farmer = Depends(get_current_farmer),
):
    return await query_nutrition_and_utilization(query)
