"""Yield and harvest prediction router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from schemas.yield_prediction import YieldPredictOut, YieldPredictRequest
from services.yield_service import predict_yield_and_harvest
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/yield", tags=["Yield & Harvest"])


@router.post("/predict", response_model=YieldPredictOut)
async def predict_yield(
    payload: YieldPredictRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await predict_yield_and_harvest(db, current_farmer, payload)
