"""Government schemes router."""

from typing import Optional

from fastapi import APIRouter, Depends

from models.farmer import Farmer
from schemas.schemes import SchemesListOut
from services.schemes_service import get_filtered_schemes
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/schemes", tags=["Government Schemes"])


@router.get("", response_model=SchemesListOut)
async def list_schemes(
    state: Optional[str] = None,
    district: Optional[str] = None,  # accepted for UI parity; filtering uses official state/category/crop rules
    category: Optional[str] = None,
    crop: Optional[str] = None,
    _current_farmer: Farmer = Depends(get_current_farmer),
):
    _ = district
    return await get_filtered_schemes(state=state, category=category, crop=crop)
