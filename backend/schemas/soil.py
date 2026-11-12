"""Soil health schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SoilRecordOut(BaseModel):
    id: int
    farmer_id: int
    source_type: str
    dataset_name: Optional[str] = None
    confidence_level: str
    status: str
    ph: Optional[float] = None
    nitrogen_kg_ha: Optional[float] = None
    phosphorus_kg_ha: Optional[float] = None
    potassium_kg_ha: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    ec_ds_m: Optional[float] = None
    sulphur_ppm: Optional[float] = None
    zinc_ppm: Optional[float] = None
    boron_ppm: Optional[float] = None
    iron_ppm: Optional[float] = None
    raw_ocr_text: Optional[str] = None
    original_filename: Optional[str] = None
    file_url: Optional[str] = None
    file_kind: Optional[str] = None
    file_mime_type: Optional[str] = None
    review_notes: Optional[str] = None
    tested_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SoilUploadExtractionOut(BaseModel):
    record: SoilRecordOut
    ocr_status: str
    ocr_note: str
    requires_review: bool = True


class SoilRecordReviewRequest(BaseModel):
    ph: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    nitrogen_kg_ha: Optional[float] = Field(default=None, ge=0.0, le=2000.0)
    phosphorus_kg_ha: Optional[float] = Field(default=None, ge=0.0, le=1000.0)
    potassium_kg_ha: Optional[float] = Field(default=None, ge=0.0, le=2000.0)
    organic_carbon_pct: Optional[float] = Field(default=None, ge=0.0, le=15.0)
    ec_ds_m: Optional[float] = Field(default=None, ge=0.0, le=30.0)
    sulphur_ppm: Optional[float] = Field(default=None, ge=0.0, le=500.0)
    zinc_ppm: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    boron_ppm: Optional[float] = Field(default=None, ge=0.0, le=50.0)
    iron_ppm: Optional[float] = Field(default=None, ge=0.0, le=500.0)
    review_notes: Optional[str] = Field(default=None, max_length=500)


class SoilEstimateRequest(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    dataset_preference: str = Field(default="auto", max_length=40)
