"""Live GPS reverse-geocoding & verified farm location router."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from integrations.geocoding_nominatim import NominatimGeocodingAdapter
from models.farmer import Farmer
from schemas.auth import FarmerProfileOut
from services.farmer_service import serialize_farmer_profile
from utils.rate_limit import rate_limit
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/location", tags=["Location & GPS"])


class VerifyLocationRequest(BaseModel):
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    gps_consent: bool = True
    continuous_gps_opt_in: bool = False
    state: str = Field(min_length=2, max_length=80)
    district: str = Field(default="", max_length=80)
    taluk: str = Field(default="", max_length=80)
    village: str = Field(default="", max_length=120)
    location_address: Optional[str] = Field(default=None, max_length=400)
    location_source: str = Field(default="gps", max_length=24)  # gps | gps_corrected | manual


@router.get(
    "/reverse",
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
async def reverse_geocode_coordinates(
    lat: float = Query(ge=-90.0, le=90.0),
    lon: float = Query(ge=-180.0, le=180.0),
    _current_farmer: Farmer = Depends(get_current_farmer),
):
    adapter = NominatimGeocodingAdapter()
    return await adapter.reverse_geocode(lat, lon)


@router.post("/verify", response_model=FarmerProfileOut)
def verify_and_save_farm_location(
    payload: VerifyLocationRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    if payload.location_source not in {"gps", "gps_corrected", "manual"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_source must be 'gps', 'gps_corrected', or 'manual'.",
        )

    current_farmer.state = payload.state.strip()
    current_farmer.district = payload.district.strip()
    current_farmer.taluk = payload.taluk.strip()
    current_farmer.village = payload.village.strip()
    current_farmer.location_address = payload.location_address.strip() if payload.location_address else None
    current_farmer.location_source = payload.location_source
    current_farmer.gps_consent = payload.gps_consent
    current_farmer.continuous_gps_opt_in = payload.gps_consent and payload.continuous_gps_opt_in

    if payload.gps_consent and payload.latitude is not None and payload.longitude is not None:
        current_farmer.latitude = round(payload.latitude, 6)
        current_farmer.longitude = round(payload.longitude, 6)
    elif not payload.gps_consent:
        current_farmer.latitude = None
        current_farmer.longitude = None
        current_farmer.continuous_gps_opt_in = False

    current_farmer.location_updated_at = datetime.now(timezone.utc)
    db.add(current_farmer)
    db.commit()
    db.refresh(current_farmer)
    return serialize_farmer_profile(current_farmer)
