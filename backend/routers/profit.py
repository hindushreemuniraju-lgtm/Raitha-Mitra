"""Profit calculator router."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.profit import ProfitCalculateRequest, ProfitScenarioOut
from services.profit_service import (
    calculate_and_optionally_save_profit,
    list_farmer_profit_scenarios,
)
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/profit", tags=["Profit Calculator"])


@router.post("/calculate", response_model=ProfitScenarioOut)
def calculate_profit(
    payload: ProfitCalculateRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return calculate_and_optionally_save_profit(db, current_farmer, payload)


@router.get("/scenarios", response_model=List[ProfitScenarioOut])
def get_saved_scenarios(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_farmer_profit_scenarios(db, current_farmer.id)
