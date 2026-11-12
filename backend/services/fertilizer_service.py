"""Fertilizer recommendation engine combining crop stage, soil deficits, and verified price lookup."""

from typing import Dict, List

from sqlalchemy.orm import Session

from integrations.fertilizer_prices import FertilizerPriceAdapter
from models.farmer import Farmer
from schemas.fertilizer import FertilizerItemOut, FertilizerRecommendationOut, FertilizerRequest
from services.soil_service import get_effective_soil_record


_BASE_NPK_PER_ACRE: Dict[str, tuple[float, float, float]] = {
    "paddy": (40.0, 20.0, 20.0),
    "rice": (40.0, 20.0, 20.0),
    "ragi": (25.0, 15.0, 10.0),
    "finger millet": (25.0, 15.0, 10.0),
    "maize": (48.0, 24.0, 16.0),
    "tomato": (50.0, 35.0, 40.0),
    "onion": (40.0, 20.0, 25.0),
    "chilli": (45.0, 25.0, 30.0),
    "groundnut": (10.0, 20.0, 15.0),
    "banana": (80.0, 30.0, 90.0),
    "mango": (35.0, 20.0, 35.0),
}

_STAGE_SPLIT: Dict[str, tuple[float, float, float]] = {
    "basal": (0.35, 1.0, 0.5),
    "germination": (0.35, 1.0, 0.5),
    "vegetative": (0.40, 0.0, 0.2),
    "flowering": (0.25, 0.0, 0.3),
    "fruiting": (0.0, 0.0, 0.3),
}


async def generate_fertilizer_plan(
    db: Session, farmer: Farmer, req: FertilizerRequest
) -> FertilizerRecommendationOut:
    acres = req.farm_size_acres or farmer.farm_size_acres or 1.0
    crop_key = req.crop_name.strip().lower()

    base_n, base_p, base_k = next(
        (vals for k, vals in _BASE_NPK_PER_ACRE.items() if k in crop_key),
        (35.0, 20.0, 20.0),
    )

    stage_key = req.growth_stage.strip().lower()
    n_split, p_split, k_split = _STAGE_SPLIT.get(stage_key, (0.35, 0.5, 0.4))

    soil = get_effective_soil_record(db, farmer.id)
    deficiencies: List[str] = []
    missing_params: List[str] = []
    n_factor, p_factor, k_factor = 1.0, 1.0, 1.0

    if soil is None:
        soil_basis = "No soil test or dataset estimate on file; using standard stage-split crop baseline."
        missing_params = ["pH", "Nitrogen", "Phosphorus", "Potassium", "Organic Carbon", "Zinc", "Boron"]
    else:
        soil_basis = (
            f"Verified {soil.source_type.replace('_', ' ')}"
            if soil.source_type != "dataset_estimate"
            else f"Dataset estimate ({soil.dataset_name})"
        )
        if soil.nitrogen_kg_ha is None:
            missing_params.append("Nitrogen")
        elif soil.nitrogen_kg_ha < 280:
            n_factor = 1.15
            deficiencies.append(f"Low Nitrogen ({soil.nitrogen_kg_ha} kg/ha)")
        elif soil.nitrogen_kg_ha > 560:
            n_factor = 0.80

        if soil.phosphorus_kg_ha is None:
            missing_params.append("Phosphorus")
        elif soil.phosphorus_kg_ha < 11:
            p_factor = 1.2
            deficiencies.append(f"Low Phosphorus ({soil.phosphorus_kg_ha} kg/ha)")
        elif soil.phosphorus_kg_ha > 25:
            p_factor = 0.8

        if soil.potassium_kg_ha is None:
            missing_params.append("Potassium")
        elif soil.potassium_kg_ha < 110:
            k_factor = 1.15
            deficiencies.append(f"Low Potassium ({soil.potassium_kg_ha} kg/ha)")
        elif soil.potassium_kg_ha > 280:
            k_factor = 0.85

        if soil.organic_carbon_pct is None:
            missing_params.append("Organic Carbon")
        elif soil.organic_carbon_pct < 0.5:
            deficiencies.append(f"Low Organic Carbon ({soil.organic_carbon_pct}%)")

        if soil.zinc_ppm is None:
            missing_params.append("Zinc")
        elif soil.zinc_ppm < 0.6:
            deficiencies.append(f"Low Zinc ({soil.zinc_ppm} ppm)")

        if soil.boron_ppm is None:
            missing_params.append("Boron")
        elif soil.boron_ppm < 0.5:
            deficiencies.append(f"Low Boron ({soil.boron_ppm} ppm)")

    target_n_ac = round(base_n * n_split * n_factor, 1)
    target_p_ac = round(base_p * p_split * p_factor, 1)
    target_k_ac = round(base_k * k_split * k_factor, 1)

    # Convert nutrient targets into DAP (18% N, 46% P2O5), Urea (46% N), MOP (60% K2O)
    dap_ac = round(target_p_ac / 0.46, 1) if target_p_ac > 0 else 0.0
    n_from_dap = dap_ac * 0.18
    urea_ac = round(max(0.0, target_n_ac - n_from_dap) / 0.46, 1) if target_n_ac > 0 else 0.0
    mop_ac = round(target_k_ac / 0.60, 1) if target_k_ac > 0 else 0.0

    price_adapter = FertilizerPriceAdapter()

    async def _build_item(
        name: str, ftype: str, per_acre: float, reason: str, timing: str
    ) -> FertilizerItemOut:
        p = await price_adapter.get_price(name, farmer.state)
        return FertilizerItemOut(
            amendment_name=name,
            amendment_type=ftype,
            quantity_per_acre_kg=round(per_acre, 1),
            quantity_kg_total=round(per_acre * acres, 1),
            reason=reason,
            application_timing=timing,
            price_inr=p["price_inr"],
            price_status=p["price_status"],
            price_source=p["price_source"],
            price_verified_date=p["price_verified_date"],
        )

    organic_plan: List[FertilizerItemOut] = [
        await _build_item(
            "Well-decomposed Farmyard Manure (FYM) / Compost",
            "organic",
            2000.0 if stage_key in {"basal", "germination"} else 500.0,
            "Builds soil organic carbon, moisture retention, and beneficial microbial activity.",
            "Incorporate into soil prior to sowing or ring-apply around root zone.",
        ),
        await _build_item(
            "Neem Cake + Biofertilizer (Azospirillum + PSB)",
            "organic",
            100.0,
            "Slow-release organic Nitrogen, root-zone Phosphorus solubilization, and soil pest deterrence.",
            "Mix with compost during basal or vegetative dressing.",
        ),
    ]

    chemical_plan: List[FertilizerItemOut] = []
    if dap_ac > 0:
        chemical_plan.append(
            await _build_item(
                "DAP (18-46-0)",
                "chemical",
                dap_ac,
                f"Supplies {target_p_ac} kg/ac P2O5 + starter Nitrogen for strong root establishment.",
                "Basal placement 4-5 cm below seed row.",
            )
        )
    if urea_ac > 0:
        chemical_plan.append(
            await _build_item(
                "Neem-Coated Urea (46% N)",
                "chemical",
                urea_ac,
                f"Supplies remaining {round(max(0.0, target_n_ac - n_from_dap), 1)} kg/ac Nitrogen for {stage_key} stage.",
                "Split top-dress onto moist soil; avoid broadcasting before heavy rain.",
            )
        )
    if mop_ac > 0:
        chemical_plan.append(
            await _build_item(
                "Muriate of Potash (MOP 60% K2O)",
                "chemical",
                mop_ac,
                f"Supplies {target_k_ac} kg/ac Potash for stalk strength, disease tolerance, and grain/fruit filling.",
                "Apply along root zone during basal or flowering split.",
            )
        )
    if soil and soil.zinc_ppm is not None and soil.zinc_ppm < 0.6:
        chemical_plan.append(
            await _build_item(
                "Zinc Sulphate Heptahydrate (21% Zn)",
                "micronutrient",
                10.0,
                f"Corrects verified Zinc deficiency ({soil.zinc_ppm} ppm < 0.6 ppm).",
                "Mix with dry soil; apply separately from DAP.",
            )
        )

    notice = (
        "Verified price feed active."
        if price_adapter.is_configured
        else "Prices marked unavailable: no verified dated fertilizer MRP feed is configured in backend .env."
    )

    return FertilizerRecommendationOut(
        crop_name=req.crop_name,
        growth_stage=stage_key,
        farm_size_acres=acres,
        soil_basis=soil_basis,
        deficiencies_detected=deficiencies,
        missing_soil_parameters=missing_params,
        organic_plan=organic_plan,
        chemical_plan=chemical_plan,
        price_notice=notice,
    )
