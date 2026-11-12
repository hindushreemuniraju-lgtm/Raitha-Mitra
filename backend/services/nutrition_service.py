"""Nutrition and utilization service (ICMR-NIN IFCT, FAO/INFOODS, USDA FDC, PubMed)."""

import asyncio
from typing import Any, Dict, List

from integrations.nutrition_pubmed import PubMedAdapter
from integrations.nutrition_usda import UsdaFoodDataAdapter
from schemas.nutrition import NutritionQueryOut


_IFCT_CATALOG: Dict[str, Dict[str, Any]] = {
    "ragi": {
        "food_name": "Finger Millet (Ragi) — Eleusine coracana",
        "source": "ICMR-NIN Indian Food Composition Tables (IFCT 2017)",
        "per_100g": {"Energy (kcal)": 320, "Protein (g)": 7.16, "Calcium (mg)": 364, "Dietary Fibre (g)": 11.18, "Iron (mg)": 4.62},
        "preparation": ["Soak, sprout, or roast before milling into flour for ragi mudde, porridge, or malt."],
        "storage": ["Dry grain below 12% moisture; stores 12-18 months in airtight steel bins or hermetic bags."],
        "value_addition": ["Sprouted ragi malt powder, ragi cookies/vermicelli, and fortified infant porridge mixes."],
    },
    "tomato": {
        "food_name": "Tomato, ripe (Solanum lycopersicum)",
        "source": "ICMR-NIN IFCT 2017",
        "per_100g": {"Energy (kcal)": 20, "Carbohydrate (g)": 2.71, "Vitamin C (mg)": 27.5, "Potassium (mg)": 204, "Lycopene / Carotenoids": "Rich source"},
        "preparation": ["Wash gently in clean water; light cooking with minimal oil increases carotenoid bioaccessibility."],
        "storage": ["Store ripe tomatoes at 12-15°C in ventilated crates; avoid chilling below 10°C which causes chilling injury."],
        "value_addition": ["Sun-dried tomato slices, puree/paste, ketchup, and dehydrated tomato powder during glut harvests."],
    },
    "paddy": {
        "food_name": "Rice, raw milled / parboiled (Oryza sativa)",
        "source": "ICMR-NIN IFCT 2017",
        "per_100g": {"Energy (kcal)": 356, "Carbohydrate (g)": 78.2, "Protein (g)": 7.9, "Dietary Fibre (g)": 2.8, "Thiamine B1 (mg)": 0.05},
        "preparation": ["Minimal rinsing preserves water-soluble B-vitamins; parboiled rice retains higher micronutrients."],
        "storage": ["Dry paddy to 12-13% moisture before milling or storage in moisture-proof sacks off the floor."],
        "value_addition": ["Parboiled rice, flattened rice (avalakki/poha), puffed rice, and rice bran oil extraction."],
    },
    "banana": {
        "food_name": "Banana, ripe (Musa paradisiaca)",
        "source": "ICMR-NIN IFCT 2017",
        "per_100g": {"Energy (kcal)": 110, "Carbohydrate (g)": 24.9, "Potassium (mg)": 362, "Dietary Fibre (g)": 2.2, "Vitamin B6 (mg)": 0.25},
        "preparation": ["Consume fresh when peel shows even yellow ripeness, or cook raw green bananas as chips/curry."],
        "storage": ["Keep harvested bunches shaded at 13-15°C with good ventilation; avoid bruising during transport."],
        "value_addition": ["Raw banana flour, vacuum-fried/baked chips, banana fig (dried slices), and stem fiber."],
    },
    "groundnut": {
        "food_name": "Groundnut / Peanut (Arachis hypogaea)",
        "source": "ICMR-NIN IFCT 2017",
        "per_100g": {"Energy (kcal)": 520, "Protein (g)": 23.6, "Total Fat (g)": 39.6, "Niacin B3 (mg)": 14.4, "Magnesium (mg)": 197},
        "preparation": ["Roast or boil thoroughly; discard moldy/shriveled kernels to avoid aflatoxin contamination."],
        "storage": ["Dry pods below 8-9% moisture quickly after harvest and store in cool, dry, ventilated conditions."],
        "value_addition": ["Cold-pressed groundnut oil, chikki, roasted salted kernels, and natural peanut butter."],
    },
}

_FAO_INFOODS_TAGS: List[str] = [
    "ENERC (Energy kcal/kJ)",
    "PROCNT (Total Protein)",
    "FAT (Total Lipid)",
    "CHOAVLDF (Available Carbohydrate)",
    "FIBTG (Total Dietary Fibre)",
    "CA (Calcium)",
    "FE (Iron)",
    "K (Potassium)",
    "VITC (Vitamin C)",
]

MEDICAL_DISCLAIMER = (
    "Educational food composition and post-harvest utilization information only. "
    "Raitha Mitra makes no medical claims and does not diagnose, treat, cure, or prevent any disease."
)


async def query_nutrition_and_utilization(query: str) -> NutritionQueryOut:
    cleaned = query.strip() or "ragi"
    lowered = cleaned.lower()

    ifct_match = next((v for k, v in _IFCT_CATALOG.items() if k in lowered), None)
    utilization = {
        "preparation": ifct_match["preparation"]
        if ifct_match
        else ["Wash produce in clean potable water and prepare using hygienic, minimal-nutrient-loss cooking methods."],
        "storage": ifct_match["storage"]
        if ifct_match
        else ["Dry grains/pulses below 12% moisture or store fresh horticulture produce in cool ventilated shade."],
        "processing_and_value_addition": ifct_match["value_addition"]
        if ifct_match
        else ["Primary grading, clean packaging, sun/solar drying, and flour/pulp processing reduce post-harvest losses."],
    }

    usda = UsdaFoodDataAdapter()
    pubmed = PubMedAdapter()
    usda_res, pubmed_res = await asyncio.gather(
        usda.search_food(cleaned),
        pubmed.search_articles(cleaned),
    )

    return NutritionQueryOut(
        crop_or_food=cleaned,
        medical_disclaimer=MEDICAL_DISCLAIMER,
        established_sources={
            "icmr_nin_ifct": ifct_match,
            "fao_infoods_tagnames": _FAO_INFOODS_TAGS,
            "usda_fdc_status": usda_res["status"],
            "usda_fdc_results": usda_res["results"],
        },
        utilization=utilization,
        preliminary_research={
            "pubmed_status": pubmed_res["status"],
            "disclaimer": "Preliminary peer-reviewed research index (PubMed). Findings may be early-stage and are not medical advice.",
            "articles": pubmed_res["articles"],
        },
    )
