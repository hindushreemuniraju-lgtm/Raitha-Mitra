"""Crop recommendation (including vegetables & fruits) and stage-wise monitoring service."""

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from models.crop import TrackedCrop
from models.farmer import Farmer
from models.media import MediaAsset
from schemas.crops import (
    CropPhotoOut,
    CropRecommendItem,
    CropRecommendRequest,
    CropRecommendResponse,
    CropStageGuidanceOut,
    TrackedCropCreate,
    TrackedCropOut,
    TrackedCropUpdate,
)
from services.soil_service import get_effective_soil_record
from utils.file_storage import (
    IMAGE_ALLOWED_EXTENSIONS,
    build_media_url,
    persist_media_asset,
    save_validated_upload,
)


_CROP_CATALOG: List[Dict] = [
    {
        "crop_name": "Finger Millet (Ragi)",
        "category": "cereal",
        "seasons": ["Kharif", "Rabi"],
        "water": ["low", "moderate"],
        "ph_range": (5.0, 8.0),
        "temp_range": (18, 34),
        "cost_level": "low",
        "duration_days": "105 - 120 days",
        "water_requirement": "Low (350 - 500 mm, drought-hardy)",
        "nutrient_needs": "N: 25 kg/ac, P2O5: 15 kg/ac, K2O: 10 kg/ac + FYM",
        "cost_range": "₹10,000 - ₹14,000 / acre",
        "yield_range": "8 - 12 quintals / acre",
        "market_note": "Strong MSP & Southern India staple demand; verify latest APMC rate in Mandi tab.",
    },
    {
        "crop_name": "Paddy (Rice)",
        "category": "cereal",
        "seasons": ["Kharif", "Rabi"],
        "water": ["high"],
        "ph_range": (5.5, 7.5),
        "temp_range": (20, 36),
        "cost_level": "moderate",
        "duration_days": "120 - 145 days",
        "water_requirement": "High (1000 - 1250 mm or canal/borewell)",
        "nutrient_needs": "N: 40-50 kg/ac, P2O5: 20 kg/ac, K2O: 20 kg/ac + Zinc",
        "cost_range": "₹18,000 - ₹25,000 / acre",
        "yield_range": "20 - 28 quintals / acre",
        "market_note": "Assured procurement & steady mandi liquidity.",
    },
    {
        "crop_name": "Red Gram (Tur / Arhar)",
        "category": "pulse",
        "seasons": ["Kharif"],
        "water": ["low", "moderate"],
        "ph_range": (6.0, 8.0),
        "temp_range": (20, 36),
        "cost_level": "low",
        "duration_days": "150 - 180 days",
        "water_requirement": "Low to Moderate (400 - 650 mm, deep taproot)",
        "nutrient_needs": "N: 10 kg/ac starter, P2O5: 20 kg/ac + Rhizobium",
        "cost_range": "₹11,000 - ₹16,000 / acre",
        "yield_range": "6 - 9 quintals / acre",
        "market_note": "High protein demand & fixes atmospheric nitrogen.",
    },
    {
        "crop_name": "Groundnut",
        "category": "oilseed",
        "seasons": ["Kharif", "Rabi", "Zaid"],
        "water": ["low", "moderate"],
        "ph_range": (6.0, 7.5),
        "temp_range": (22, 35),
        "cost_level": "moderate",
        "duration_days": "105 - 125 days",
        "water_requirement": "Moderate (500 - 650 mm, well-drained sandy loam)",
        "nutrient_needs": "N: 10 kg/ac, P2O5: 20 kg/ac, Gypsum 200 kg/ac at flowering",
        "cost_range": "₹16,000 - ₹22,000 / acre",
        "yield_range": "8 - 12 quintals / acre",
        "market_note": "High edible oil & confectionery demand.",
    },
    {
        "crop_name": "Tomato (Hybrid)",
        "category": "vegetable",
        "seasons": ["Kharif", "Rabi", "Zaid"],
        "water": ["moderate", "high"],
        "ph_range": (6.0, 7.2),
        "temp_range": (18, 32),
        "cost_level": "high",
        "duration_days": "110 - 135 days",
        "water_requirement": "Moderate to High (drip irrigation recommended)",
        "nutrient_needs": "N: 50 kg/ac, P2O5: 35 kg/ac, K2O: 40 kg/ac + Calcium/Boron",
        "cost_range": "₹35,000 - ₹55,000 / acre",
        "yield_range": "100 - 160 quintals / acre",
        "market_note": "High return potential; prices fluctuate seasonally—check Mandi history.",
    },
    {
        "crop_name": "Onion",
        "category": "vegetable",
        "seasons": ["Kharif", "Rabi"],
        "water": ["moderate"],
        "ph_range": (6.0, 7.5),
        "temp_range": (15, 32),
        "cost_level": "moderate",
        "duration_days": "110 - 130 days",
        "water_requirement": "Moderate (450 - 600 mm; stop irrigation 15 days pre-harvest)",
        "nutrient_needs": "N: 40 kg/ac, P2O5: 20 kg/ac, K2O: 25 kg/ac + Sulphur",
        "cost_range": "₹25,000 - ₹36,000 / acre",
        "yield_range": "75 - 110 quintals / acre",
        "market_note": "Rabi bulbs store well for staggered market sale.",
    },
    {
        "crop_name": "Green Chilli",
        "category": "vegetable",
        "seasons": ["Kharif", "Rabi", "Zaid"],
        "water": ["moderate"],
        "ph_range": (6.0, 7.5),
        "temp_range": (20, 35),
        "cost_level": "moderate",
        "duration_days": "150 - 180 days",
        "water_requirement": "Moderate (avoid waterlogging; drip + mulch ideal)",
        "nutrient_needs": "N: 45 kg/ac, P2O5: 25 kg/ac, K2O: 30 kg/ac",
        "cost_range": "₹28,000 - ₹42,000 / acre",
        "yield_range": "40 - 65 quintals fresh / acre",
        "market_note": "Multiple pickings stabilize cash flow.",
    },
    {
        "crop_name": "Okra (Bhindi)",
        "category": "vegetable",
        "seasons": ["Kharif", "Zaid"],
        "water": ["moderate"],
        "ph_range": (6.0, 7.5),
        "temp_range": (22, 38),
        "cost_level": "low",
        "duration_days": "90 - 105 days",
        "water_requirement": "Moderate (light irrigation every 5-7 days)",
        "nutrient_needs": "N: 30 kg/ac, P2O5: 20 kg/ac, K2O: 15 kg/ac",
        "cost_range": "₹16,000 - ₹24,000 / acre",
        "yield_range": "35 - 50 quintals / acre",
        "market_note": "Fast harvest turnaround starting 45 days after sowing.",
    },
    {
        "crop_name": "Banana (Grand Naine / Yelakki)",
        "category": "fruit",
        "seasons": ["Kharif", "Rabi", "Zaid"],
        "water": ["high"],
        "ph_range": (6.0, 7.8),
        "temp_range": (18, 36),
        "cost_level": "high",
        "duration_days": "330 - 365 days",
        "water_requirement": "High (drip fertigation ideal)",
        "nutrient_needs": "High Potassium & Nitrogen split across vegetative/shooting stages",
        "cost_range": "₹65,000 - ₹95,000 / acre",
        "yield_range": "220 - 320 quintals / acre",
        "market_note": "Consistent year-round domestic & festival demand.",
    },
    {
        "crop_name": "Papaya (Red Lady / Taiwan)",
        "category": "fruit",
        "seasons": ["Kharif", "Rabi", "Zaid"],
        "water": ["moderate"],
        "ph_range": (6.0, 7.2),
        "temp_range": (20, 36),
        "cost_level": "moderate",
        "duration_days": "270 - 330 days to peak fruiting",
        "water_requirement": "Moderate (strictly well-drained; root rot sensitive)",
        "nutrient_needs": "Balanced NPK + Boron 0.1% spray for fruit set",
        "cost_range": "₹40,000 - ₹60,000 / acre",
        "yield_range": "180 - 260 quintals / acre",
        "market_note": "High market value in urban vegetable/fruit mandis.",
    },
    {
        "crop_name": "Pomegranate (Bhagwa)",
        "category": "fruit",
        "seasons": ["Kharif", "Rabi"],
        "water": ["low", "moderate"],
        "ph_range": (6.5, 8.2),
        "temp_range": (18, 38),
        "cost_level": "high",
        "duration_days": "Perennial (first commercial harvest 18 months)",
        "water_requirement": "Low to Moderate (well-suited to semi-arid Deccan belts)",
        "nutrient_needs": "FYM + split NPK + micronutrients",
        "cost_range": "₹55,000 - ₹85,000 / acre",
        "yield_range": "50 - 80 quintals / acre",
        "market_note": "Premium fruit value with export & domestic buyer interest.",
    },
]


def recommend_crops_for_farmer(
    db: Session, farmer: Farmer, req: CropRecommendRequest
) -> CropRecommendResponse:
    soil = get_effective_soil_record(db, farmer.id)
    missing_fields: List[str] = []
    if soil is None:
        soil_source = "No soil record on file (using seasonal & water matching only)"
        missing_fields = ["pH", "Nitrogen", "Phosphorus", "Potassium", "Organic Carbon"]
    else:
        soil_source = (
            f"Verified {soil.source_type.replace('_', ' ')}"
            if soil.source_type != "dataset_estimate"
            else f"Dataset estimate ({soil.dataset_name}, confidence: {soil.confidence_level})"
        )
        if soil.ph is None:
            missing_fields.append("pH")
        if soil.nitrogen_kg_ha is None:
            missing_fields.append("Nitrogen")
        if soil.phosphorus_kg_ha is None:
            missing_fields.append("Phosphorus")
        if soil.potassium_kg_ha is None:
            missing_fields.append("Potassium")

    state_used = req.state_override or farmer.state or "Karnataka"
    ranked: List[CropRecommendItem] = []

    for item in _CROP_CATALOG:
        if not req.include_horticulture and item["category"] in {"vegetable", "fruit"}:
            continue

        score = 55
        reasons: List[str] = []

        if req.season in item["seasons"]:
            score += 18
            reasons.append(f"Well-suited for {req.season} sowing window.")
        else:
            score -= 12

        if req.water_availability in item["water"]:
            score += 15
            reasons.append(f"Matches your {req.water_availability} water availability.")
        else:
            score -= 10
            reasons.append(f"Caution: crop prefers {'/'.join(item['water'])} water availability.")

        if soil and soil.ph is not None:
            low_ph, high_ph = item["ph_range"]
            if low_ph <= soil.ph <= high_ph:
                score += 10
                reasons.append(f"Soil pH {soil.ph:.1f} falls inside ideal range ({low_ph}-{high_ph}).")
            else:
                score -= 8
                reasons.append(f"Soil pH {soil.ph:.1f} is outside ideal {low_ph}-{high_ph}; lime/gypsum check advised.")

        if req.avg_temp_c is not None:
            t_min, t_max = item["temp_range"]
            if t_min <= req.avg_temp_c <= t_max:
                score += 7
                reasons.append(f"Temperature {req.avg_temp_c:.1f}°C suits crop canopy growth.")
            else:
                score -= 6

        if req.budget_level == item["cost_level"]:
            score += 5
            reasons.append(f"Aligns with your {req.budget_level} input budget.")

        ranked.append(
            CropRecommendItem(
                crop_name=item["crop_name"],
                category=item["category"],
                suitability_score=max(20, min(98, score)),
                reasons=reasons,
                duration_days=item["duration_days"],
                water_requirement=item["water_requirement"],
                nutrient_needs=item["nutrient_needs"],
                estimated_cost_per_acre_inr=item["cost_range"],
                expected_yield_per_acre=item["yield_range"],
                market_value_note=item["market_note"],
            )
        )

    ranked.sort(key=lambda x: x.suitability_score, reverse=True)
    return CropRecommendResponse(
        season=req.season,
        location_summary=f"{farmer.district or farmer.village or state_used}, {state_used}",
        soil_source_used=soil_source,
        missing_soil_fields=missing_fields,
        recommendations=ranked[:8],
    )


_STAGE_GUIDANCE: Dict[str, Dict] = {
    "germination": {
        "stage_label": "Germination & Establishment",
        "day_range": "Days 0 - 20",
        "irrigation_advice": "Keep topsoil moist with light irrigation; avoid crusting or standing water.",
        "nutrient_advice": "Ensure basal Phosphorus + FYM/compost placement near root zone.",
        "cultivation_tasks": [
            "Inspect germination percentage at Day 7-10 and gap-fill sparse rows",
            "Check seedlings for damping-off or cutworm damage",
            "Keep field bunds clear of early competing weeds",
        ],
    },
    "vegetative": {
        "stage_label": "Vegetative Canopy Growth",
        "day_range": "Days 21 - 50",
        "irrigation_advice": "Maintain consistent root-zone moisture; irrigate at 50% available soil moisture depletion.",
        "nutrient_advice": "Apply first split top-dressing of Nitrogen based on soil test status.",
        "cultivation_tasks": [
            "Perform inter-cultivation / hand weeding before canopy closure",
            "Install yellow sticky traps or pheromone traps for early pest scouting",
            "Verify lower leaves for N/Mg yellowing before top-dressing",
        ],
    },
    "flowering": {
        "stage_label": "Flowering & Pollination",
        "day_range": "Days 51 - 80",
        "irrigation_advice": "Avoid moisture stress during bud initiation and flowering; avoid midday overhead spraying.",
        "nutrient_advice": "Support Potassium, Boron, and Calcium uptake for flower retention.",
        "cultivation_tasks": [
            "Avoid broad-spectrum insecticides during peak pollinator activity",
            "Scout flowers and shoots for borers, thrips, or fungal spots",
            "Provide staking/earthing-up where applicable (tomato, chilli, banana)",
        ],
    },
    "fruiting": {
        "stage_label": "Fruit Set & Grain Filling",
        "day_range": "Days 81 - 110",
        "irrigation_advice": "Steady drip/furrow irrigation prevents fruit cracking and shrivelled grain.",
        "nutrient_advice": "Foliar Potassium (SOP) or Potash support enhances weight, Brix, and shine.",
        "cultivation_tasks": [
            "Remove severely diseased leaves/fruits safely away from plot",
            "Inspect fruits/pods for borer entry holes and rot",
            "Arrange clean harvesting crates and tarpaulins ahead of maturity",
        ],
    },
    "maturity": {
        "stage_label": "Maturity & Harvest Preparation",
        "day_range": "Days 111+",
        "irrigation_advice": "Gradually taper irrigation 7-14 days before harvest (crop dependent) to improve storage quality.",
        "nutrient_advice": "Do not apply fresh Nitrogen; observe safe pre-harvest intervals for any prior sprays.",
        "cultivation_tasks": [
            "Check physiological maturity indicators (moisture %, colour break, firmness)",
            "Monitor 5-day weather forecast to schedule dry-weather harvest",
            "Grade and pack produce cleanly by size and ripeness before mandi dispatch",
        ],
    },
}


def compute_stage_from_days(days: int) -> str:
    if days <= 20:
        return "germination"
    if days <= 50:
        return "vegetative"
    if days <= 80:
        return "flowering"
    if days <= 110:
        return "fruiting"
    return "maturity"


def enrich_tracked_crop(crop: TrackedCrop, db: Optional[Session] = None) -> TrackedCropOut:
    days = max(0, (date.today() - crop.sowing_date).days)
    stage_key = crop.current_stage if crop.current_stage in _STAGE_GUIDANCE else compute_stage_from_days(days)
    g = _STAGE_GUIDANCE[stage_key]

    asset_ids = [str(aid) for aid in (crop.photo_asset_ids or []) if aid]
    filename_map: Dict[str, str] = {}
    if db is not None and asset_ids:
        rows = (
            db.query(MediaAsset.id, MediaAsset.original_filename)
            .filter(MediaAsset.id.in_(asset_ids), MediaAsset.farmer_id == crop.farmer_id)
            .all()
        )
        filename_map = {str(r[0]): str(r[1]) for r in rows}

    photos = [
        CropPhotoOut(
            asset_id=aid,
            url=build_media_url(aid, crop.farmer_id) or "",
            original_filename=filename_map.get(aid, "crop-photo.jpg"),
        )
        for aid in asset_ids
    ]

    return TrackedCropOut(
        id=crop.id,
        farmer_id=crop.farmer_id,
        crop_name=crop.crop_name,
        variety=crop.variety,
        category=crop.category,
        sowing_date=crop.sowing_date,
        acreage=crop.acreage,
        irrigation_type=crop.irrigation_type,
        current_stage=stage_key,
        completed_tasks=list(crop.completed_tasks or []),
        photos=photos,
        status=crop.status,
        notes=crop.notes,
        days_since_sowing=days,
        stage_guidance=CropStageGuidanceOut(stage_key=stage_key, **g),
    )


def create_tracked_crop(db: Session, farmer: Farmer, payload: TrackedCropCreate) -> TrackedCropOut:
    days = max(0, (date.today() - payload.sowing_date).days)
    stage = compute_stage_from_days(days)
    crop = TrackedCrop(
        farmer_id=farmer.id,
        crop_name=payload.crop_name.strip(),
        variety=payload.variety.strip() if payload.variety else None,
        category=payload.category.strip(),
        sowing_date=payload.sowing_date,
        acreage=payload.acreage,
        irrigation_type=payload.irrigation_type.strip(),
        current_stage=stage,
        completed_tasks=[],
        photo_asset_ids=[],
        status="active",
        notes=payload.notes,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return enrich_tracked_crop(crop, db)


def list_tracked_crops(db: Session, farmer_id: int) -> List[TrackedCropOut]:
    rows = (
        db.query(TrackedCrop)
        .filter(TrackedCrop.farmer_id == farmer_id)
        .order_by(TrackedCrop.created_at.desc())
        .all()
    )
    return [enrich_tracked_crop(r, db) for r in rows]


def update_tracked_crop(
    db: Session, farmer_id: int, crop_id: int, payload: TrackedCropUpdate
) -> TrackedCropOut:
    crop = (
        db.query(TrackedCrop)
        .filter(TrackedCrop.id == crop_id, TrackedCrop.farmer_id == farmer_id)
        .first()
    )
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked crop not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(crop, field, value)
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return enrich_tracked_crop(crop, db)


async def upload_tracked_crop_photo(
    db: Session, farmer: Farmer, crop_id: int, file: UploadFile
) -> TrackedCropOut:
    crop = (
        db.query(TrackedCrop)
        .filter(TrackedCrop.id == crop_id, TrackedCrop.farmer_id == farmer.id)
        .first()
    )
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked crop not found.")

    safe_name, _, raw_bytes = await save_validated_upload(
        file, subdir="crop_photos", allowed_extensions=IMAGE_ALLOWED_EXTENSIONS
    )
    asset = persist_media_asset(
        db,
        farmer_id=farmer.id,
        category="crop_photos",
        safe_filename=safe_name,
        original_filename=Path(file.filename or safe_name).name,
        content=raw_bytes,
    )
    existing = list(crop.photo_asset_ids or [])
    crop.photo_asset_ids = [asset.id, *existing]
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return enrich_tracked_crop(crop, db)


def delete_tracked_crop(db: Session, farmer_id: int, crop_id: int) -> None:
    crop = (
        db.query(TrackedCrop)
        .filter(TrackedCrop.id == crop_id, TrackedCrop.farmer_id == farmer_id)
        .first()
    )
    if crop is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracked crop not found.")
    db.delete(crop)
    db.commit()
