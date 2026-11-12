"""Pest and disease scan schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DiseaseScanOut(BaseModel):
    id: int
    farmer_id: int
    crop_name: Optional[str] = None
    adapter_used: str
    confidence: Optional[float] = None
    status: str
    diagnosis_name: Optional[str] = None
    symptoms: List[str]
    organic_treatments: List[str]
    chemical_treatments: List[str]
    precautions: List[str]
    raw_summary: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
