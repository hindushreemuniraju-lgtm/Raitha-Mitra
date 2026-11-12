"""Modular agronomic Yield & Harvest Prediction service."""

from datetime import timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

from integrations.google_agri import GoogleAgriAdapter
from models.farmer import Farmer
from schemas.yield_prediction import YieldPredictOut, YieldPredictRequest
from services.soil_service import get_effective_soil_record


_CROP_BASELINE: Dict[str, Dict] = {
    "paddy": {"qtl_per_acre": (18.0, 24.0, 29.0), "days": (120, 135), "maturity": "80-85% straw-colored panicles and ~20% grain moisture"},
    "rice": {"qtl_per_acre": (18.0, 24.0, 29.0), "days": (120, 135), "maturity": "80-85% straw-colored panicles and ~20% grain moisture"},
    "ragi": {"qtl_per_acre": (7.0, 10.0, 13.0), "days": (105, 120), "maturity": "Brown-turned earheads and hard dry threshable grain"},
    "finger millet": {"qtl_per_acre": (7.0, 10.0, 13.0), "days": (105, 120), "maturity": "Brown-turned earheads and hard dry threshable grain"},
    "maize": {"qtl_per_acre": (16.0, 22.0, 28.0), "days": (100, 115), "maturity": "Dry husks and black layer formation at kernel base"},
    "tomato": {"qtl_per_acre": (95.0, 130.0, 165.0), "days": (75, 115), "maturity": "Breaker-to-pink stage for distant mandi; red-ripe for local fresh sale"},
    "onion": {"qtl_per_acre": (70.0, 95.0, 120.0), "days": (110, 125), "maturity": "50-75% neck fall (top drying) followed by 7-10 days field curing"},
    "chilli": {"qtl_per_acre": (35.0, 50.0, 65.0), "days": (75, 150), "maturity": "Firm glossy pods (green) or full deep-red color before dry picking"},
    "groundnut": {"qtl_per_acre": (7.0, 10.0, 13.0), "days": (105, 120), "maturity": "Inner pod shell darkening (70-80% mature pods)"},
    "banana": {"qtl_per_acre": (210.0, 260.0, 310.0), "days": (320, 355), "maturity": "Rounded finger angles (75-80% maturity) before ripening yellowing"},
}


async def predict_yield_and_harvest(
    db: Session, farmer: Farmer, req: YieldPredictRequest
) -> YieldPredictOut:
    crop_key = req.crop_name.strip().lower()
    baseline = next(
        (v for k, v in _CROP_BASELINE.items() if k in crop_key),
        {
            "qtl_per_acre": (10.0, 14.0, 18.0),
            "days": (105, 125),
            "maturity": "Physiological maturity markers (seed/fruit firmness and moisture drop)",
        },
    )

    q_low, q_exp, q_high = baseline["qtl_per_acre"]
    multiplier = 1.0
    confidence = 68
    risks: List[str] = []

    # Irrigation & rainfall factor
    if req.irrigation_type.lower() == "drip":
        multiplier += 0.08
        confidence += 5
    elif req.irrigation_type.lower() == "rainfed":
        if req.rainfall_adequacy == "deficit":
            multiplier -= 0.18
            risks.append("Rainfed moisture deficit lowers expected grain/fruit weight.")
        elif req.rainfall_adequacy == "excess":
            multiplier -= 0.12
            risks.append("Excess moisture increases root-zone stress and harvest rot risk.")

    # Pest pressure factor
    pest_lvl = req.pest_status.lower()
    if pest_lvl == "moderate":
        multiplier -= 0.12
        risks.append("Moderate pest/disease pressure; timely IPM intervention needed.")
    elif pest_lvl == "severe":
        multiplier -= 0.25
        confidence -= 8
        risks.append("Severe pest/disease pressure significantly widens yield uncertainty.")

    # Soil health factor
    soil = get_effective_soil_record(db, farmer.id)
    if soil is not None:
        confidence += 10 if soil.source_type != "dataset_estimate" else 4
        if soil.ph is not None and (soil.ph < 5.2 or soil.ph > 8.3):
            multiplier -= 0.08
            risks.append(f"Soil pH ({soil.ph:.1f}) limits nutrient availability.")
        if soil.organic_carbon_pct is not None and soil.organic_carbon_pct >= 0.6:
            multiplier += 0.05
    else:
        risks.append("No soil report on file; adding a Soil Health Card tightens yield confidence.")

    multiplier = max(0.45, min(1.30, multiplier))
    acreage = req.acreage
    min_tot = round(q_low * multiplier * acreage, 1)
    exp_tot = round(q_exp * multiplier * acreage, 1)
    max_tot = round(q_high * multiplier * acreage, 1)

    d_start, d_end = baseline["days"]
    h_start = req.sowing_date + timedelta(days=d_start)
    h_end = req.sowing_date + timedelta(days=d_end)

    # Google Agricultural Understanding (ALU/AMED) optional metadata enrichment
    google_adapter = GoogleAgriAdapter()
    google_res = await google_adapter.lookup_landscape_metadata(
        farmer.latitude if farmer.gps_consent else None,
        farmer.longitude if farmer.gps_consent else None,
    )

    confidence = max(35, min(90, confidence))
    conf_label = "High" if confidence >= 78 else "Moderate" if confidence >= 60 else "Low"

    return YieldPredictOut(
        crop_name=req.crop_name,
        acreage=acreage,
        yield_min_qtl_total=min_tot,
        yield_expected_qtl_total=exp_tot,
        yield_max_qtl_total=max_tot,
        yield_per_acre_range_qtl=f"{round(q_low * multiplier, 1)} - {round(q_high * multiplier, 1)} qtl/acre",
        confidence_pct=confidence,
        confidence_label=conf_label,
        harvest_window_start=h_start.isoformat(),
        harvest_window_end=h_end.isoformat(),
        maturity_basis=[
            baseline["maturity"],
            "Harvest window is anchored to physiological crop maturity & post-harvest quality, not market price alone.",
            "Confirm dry 48-hour forecast in Weather tab before cutting/picking.",
        ],
        risk_factors=risks or ["No major agronomic risks flagged from current inputs."],
        google_agri_status=google_res["status"],
        google_agri_note=google_res["note"],
        google_landscape_metadata=google_res["metadata"],
    )
