"""Authentication and farmer profile schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from utils.security import normalize_mobile


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    mobile: str = Field(min_length=10, max_length=20)
    email: Optional[str] = Field(default=None, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    state: str = Field(default="Karnataka", min_length=2, max_length=80)
    district: str = Field(default="", max_length=80)
    taluk: str = Field(default="", max_length=80)
    village: str = Field(default="", max_length=120)
    location_address: Optional[str] = Field(default=None, max_length=400)
    location_source: str = Field(default="manual", max_length=24)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    gps_consent: bool = False
    continuous_gps_opt_in: bool = False
    farm_size_acres: float = Field(default=2.0, gt=0.0, le=10000.0)
    soil_type: Optional[str] = Field(default=None, max_length=80)
    main_crops: List[str] = Field(default_factory=list)
    preferred_language: str = Field(default="kn-IN", max_length=16)
    farmer_category: str = Field(default="small", max_length=40)

    @field_validator("mobile")
    @classmethod
    def _validate_mobile(cls, value: str) -> str:
        normalized = normalize_mobile(value)
        if len(normalized) < 10:
            raise ValueError("Please enter a valid 10-digit Indian mobile number.")
        return normalized

    @field_validator("email")
    @classmethod
    def _clean_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip().lower()
        return stripped or None


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=160, description="Registered mobile or email")
    password: str = Field(min_length=1, max_length=128)


class FarmerProfileOut(BaseModel):
    id: int
    full_name: str
    mobile: str
    email: Optional[str] = None
    state: str
    district: str
    taluk: str = ""
    village: str
    location_address: Optional[str] = None
    location_source: str = "manual"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_consent: bool
    continuous_gps_opt_in: bool = False
    location_updated_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    farm_size_acres: float
    soil_type: Optional[str] = None
    main_crops: List[str]
    preferred_language: str
    farmer_category: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FarmerProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    email: Optional[str] = Field(default=None, max_length=160)
    state: Optional[str] = Field(default=None, min_length=2, max_length=80)
    district: Optional[str] = Field(default=None, max_length=80)
    taluk: Optional[str] = Field(default=None, max_length=80)
    village: Optional[str] = Field(default=None, max_length=120)
    location_address: Optional[str] = Field(default=None, max_length=400)
    location_source: Optional[str] = Field(default=None, max_length=24)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    gps_consent: Optional[bool] = None
    continuous_gps_opt_in: Optional[bool] = None
    farm_size_acres: Optional[float] = Field(default=None, gt=0.0, le=10000.0)
    soil_type: Optional[str] = Field(default=None, max_length=80)
    main_crops: Optional[List[str]] = None
    preferred_language: Optional[str] = Field(default=None, max_length=16)
    farmer_category: Optional[str] = Field(default=None, max_length=40)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    farmer: FarmerProfileOut
