"""Farmer dashboard aggregation router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.farmer import Farmer
from services.dashboard_service import build_dashboard_summary
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await build_dashboard_summary(db, current_farmer)
