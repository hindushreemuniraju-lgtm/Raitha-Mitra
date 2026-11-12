"""Farmer profile management and photo upload service."""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.farmer import Farmer
from schemas.auth import FarmerProfileOut, FarmerProfileUpdate
from utils.file_storage import (
    IMAGE_ALLOWED_EXTENSIONS,
    build_media_url,
    persist_media_asset,
    save_validated_upload,
)


def serialize_farmer_profile(farmer: Farmer) -> FarmerProfileOut:
    """Serialize Farmer ORM object including signed profile photo URL without leaking paths."""
    return FarmerProfileOut(
        id=farmer.id,
        full_name=farmer.full_name,
        mobile=farmer.mobile,
        email=farmer.email,
        state=farmer.state,
        district=farmer.district,
        taluk=farmer.taluk or "",
        village=farmer.village,
        location_address=farmer.location_address,
        location_source=farmer.location_source or "manual",
        latitude=farmer.latitude,
        longitude=farmer.longitude,
        gps_consent=bool(farmer.gps_consent),
        continuous_gps_opt_in=bool(farmer.continuous_gps_opt_in),
        location_updated_at=farmer.location_updated_at,
        avatar_url=build_media_url(farmer.avatar_asset_id, farmer.id),
        farm_size_acres=farmer.farm_size_acres,
        soil_type=farmer.soil_type,
        main_crops=list(farmer.main_crops or []),
        preferred_language=farmer.preferred_language,
        farmer_category=farmer.farmer_category,
        created_at=farmer.created_at,
        updated_at=farmer.updated_at,
    )


def update_farmer_profile(db: Session, farmer: Farmer, payload: FarmerProfileUpdate) -> FarmerProfileOut:
    """Apply validated profile updates scoped strictly to the authenticated farmer."""
    data = payload.model_dump(exclude_unset=True)

    # Enforce opt-in GPS rule: clear coordinates & continuous tracking if consent is revoked
    if "gps_consent" in data and data["gps_consent"] is False:
        farmer.latitude = None
        farmer.longitude = None
        farmer.continuous_gps_opt_in = False
        farmer.location_source = "manual"
        data.pop("latitude", None)
        data.pop("longitude", None)
        data.pop("continuous_gps_opt_in", None)
    elif ("latitude" in data or "longitude" in data) and not (
        data.get("gps_consent", farmer.gps_consent)
    ):
        data.pop("latitude", None)
        data.pop("longitude", None)

    if "main_crops" in data and data["main_crops"] is not None:
        data["main_crops"] = [c.strip() for c in data["main_crops"] if c and c.strip()]

    location_keys = {"state", "district", "taluk", "village", "latitude", "longitude", "location_address"}
    if any(k in data for k in location_keys):
        farmer.location_updated_at = datetime.now(timezone.utc)

    for field, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(farmer, field, value)

    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return serialize_farmer_profile(farmer)


async def upload_farmer_photo(db: Session, farmer: Farmer, file: UploadFile) -> FarmerProfileOut:
    """Validate and persistently store a farmer profile photograph."""
    safe_name, _, raw_bytes = await save_validated_upload(
        file, subdir="profile_photos", allowed_extensions=IMAGE_ALLOWED_EXTENSIONS
    )
    asset = persist_media_asset(
        db,
        farmer_id=farmer.id,
        category="profile_photos",
        safe_filename=safe_name,
        original_filename=Path(file.filename or safe_name).name,
        content=raw_bytes,
    )
    farmer.avatar_asset_id = asset.id
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return serialize_farmer_profile(farmer)
