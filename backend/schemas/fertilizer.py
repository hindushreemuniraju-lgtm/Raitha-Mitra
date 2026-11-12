"""Fertilizer recommendation schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class FertilizerRequest(BaseModel):
    crop_name: str = Field(min_length=2, max_length=80)
    growth_stage: str = Field(default="basal", max_length=40)
    farm_size_acres: Optional[float] = Field(default=None, gt=0.0, le=5000.0)


class FertilizerItemOut(BaseModel):
    amendment_name: str
    amendment_type: str
    quantity_kg_total: float
    quantity_per_acre_kg: float
    reason: str
    application_timing: str
    price_inr: Optional[float] = None
    price_status: str
    price_source: Optional[str] = None
    price_verified_date: Optional[str] = None


class FertilizerRecommendationOut(BaseModel):
    crop_name: str
    growth_stage: str
    farm_size_acres: float
    soil_basis: str
    deficiencies_detected: List[str]
    missing_soil_parameters: List[str]
    organic_plan: List[FertilizerItemOut]
    chemical_plan: List[FertilizerItemOut]
    price_notice: str
