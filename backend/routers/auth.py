"""Authentication endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from services.auth_service import authenticate_farmer, register_farmer
from services.farmer_service import serialize_farmer_profile
from utils.rate_limit import rate_limit


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=15, window_seconds=60))],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    token, farmer = register_farmer(db, payload)
    return TokenResponse(access_token=token, farmer=serialize_farmer_profile(farmer))


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(max_requests=25, window_seconds=60))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token, farmer = authenticate_farmer(db, payload)
    return TokenResponse(access_token=token, farmer=serialize_farmer_profile(farmer))
