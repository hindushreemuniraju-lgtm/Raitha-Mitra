"""Mandi prices router."""

from typing import Optional

from fastapi import APIRouter, Depends

from models.farmer import Farmer
from schemas.mandi import MandiResponseOut
from services.mandi_service import get_mandi_prices_report
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/mandi", tags=["Mandi Prices"])


@router.get("", response_model=MandiResponseOut)
async def list_mandi_prices(
    commodity: Optional[str] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    date: Optional[str] = None,
    include_demo: bool = False,
    _current_farmer: Farmer = Depends(get_current_farmer),
):
    return await get_mandi_prices_report(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        date_str=date,
        include_demo=include_demo,
    )
