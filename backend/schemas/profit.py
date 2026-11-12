"""Profit calculator schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProfitCalculateRequest(BaseModel):
    crop_name: str = Field(min_length=2, max_length=80)
    farm_size_acres: float = Field(gt=0.0, le=5000.0)
    seed_cost: float = Field(default=0.0, ge=0.0)
    fertilizer_cost: float = Field(default=0.0, ge=0.0)
    pesticide_cost: float = Field(default=0.0, ge=0.0)
    labour_cost: float = Field(default=0.0, ge=0.0)
    irrigation_cost: float = Field(default=0.0, ge=0.0)
    transport_cost: float = Field(default=0.0, ge=0.0)
    other_cost: float = Field(default=0.0, ge=0.0)
    expected_yield_qtl_per_acre: float = Field(gt=0.0, le=1000.0)
    expected_price_per_qtl: float = Field(gt=0.0, le=1000000.0)
    save_scenario: bool = True


class ProfitScenarioOut(BaseModel):
    id: Optional[int] = None
    crop_name: str
    farm_size_acres: float
    total_cost: float
    expected_revenue: float
    net_profit: float
    profit_per_acre: float
    margin_pct: float
    breakeven_price_per_qtl: float
    scenarios: List[Dict[str, Any]]
    cost_breakdown: List[Dict[str, Any]]
    disclaimer: str
    created_at: Optional[datetime] = None
