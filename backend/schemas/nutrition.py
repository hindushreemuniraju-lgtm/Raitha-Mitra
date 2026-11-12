"""Nutrition and utilization schemas."""

from typing import Any, Dict, List

from pydantic import BaseModel


class NutritionQueryOut(BaseModel):
    crop_or_food: str
    medical_disclaimer: str
    established_sources: Dict[str, Any]
    utilization: Dict[str, List[str]]
    preliminary_research: Dict[str, Any]
