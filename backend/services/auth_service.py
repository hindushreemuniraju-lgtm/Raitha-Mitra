"""Authentication business logic."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.farmer import Farmer
from schemas.auth import LoginRequest, RegisterRequest
from utils.security import (
    create_access_token,
    hash_password,
    normalize_mobile,
    verify_password,
)


def register_farmer(db: Session, payload: RegisterRequest) -> tuple[str, Farmer]:
    """Create a new farmer account and return (jwt_token, farmer)."""
    existing_mobile = db.query(Farmer).filter(Farmer.mobile == payload.mobile).first()
    if existing_mobile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this mobile number already exists.",
        )

    if payload.email:
        existing_email = db.query(Farmer).filter(Farmer.email == payload.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

    lat = payload.latitude if payload.gps_consent else payload.latitude
    lon = payload.longitude if payload.gps_consent else payload.longitude
    if not payload.gps_consent and (payload.latitude is not None or payload.longitude is not None):
        # GPS is strictly opt-in with explicit consent
        lat = None
        lon = None

    farmer = Farmer(
        full_name=payload.full_name.strip(),
        mobile=payload.mobile,
        email=payload.email,
        password_hash=hash_password(payload.password),
        state=payload.state.strip(),
        district=payload.district.strip(),
        village=payload.village.strip(),
        latitude=lat,
        longitude=lon,
        gps_consent=payload.gps_consent,
        farm_size_acres=payload.farm_size_acres,
        soil_type=payload.soil_type.strip() if payload.soil_type else None,
        main_crops=[c.strip() for c in payload.main_crops if c.strip()],
        preferred_language=payload.preferred_language,
        farmer_category=payload.farmer_category,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    token = create_access_token(farmer.id)
    return token, farmer


def authenticate_farmer(db: Session, payload: LoginRequest) -> tuple[str, Farmer]:
    """Verify farmer credentials by mobile or email and return (jwt_token, farmer)."""
    identifier = payload.identifier.strip()
    if "@" in identifier:
        farmer = db.query(Farmer).filter(Farmer.email == identifier.lower()).first()
    else:
        normalized = normalize_mobile(identifier)
        farmer = db.query(Farmer).filter(Farmer.mobile == normalized).first()

    if farmer is None or not verify_password(payload.password, farmer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile/email or password.",
        )

    token = create_access_token(farmer.id)
    return token, farmer
