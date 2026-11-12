"""Farmer profile management service."""

from sqlalchemy.orm import Session

from models.farmer import Farmer
from schemas.auth import FarmerProfileUpdate


def update_farmer_profile(db: Session, farmer: Farmer, payload: FarmerProfileUpdate) -> Farmer:
    """Apply validated profile updates scoped strictly to the authenticated farmer."""
    data = payload.model_dump(exclude_unset=True)

    # Enforce opt-in GPS rule: clear coordinates if consent is revoked
    if "gps_consent" in data and data["gps_consent"] is False:
        farmer.latitude = None
        farmer.longitude = None
        data.pop("latitude", None)
        data.pop("longitude", None)
    elif ("latitude" in data or "longitude" in data) and not (
        data.get("gps_consent", farmer.gps_consent)
    ):
        data.pop("latitude", None)
        data.pop("longitude", None)

    if "main_crops" in data and data["main_crops"] is not None:
        data["main_crops"] = [c.strip() for c in data["main_crops"] if c and c.strip()]

    for field, value in data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(farmer, field, value)

    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer
