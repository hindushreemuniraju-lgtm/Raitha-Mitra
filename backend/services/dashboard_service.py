"""Dashboard aggregation service."""

from sqlalchemy.orm import Session

from config import get_settings
from models.farmer import Farmer
from schemas.yield_prediction import YieldPredictRequest
from services.crop_service import list_tracked_crops
from services.disease_service import list_disease_scans
from services.mandi_service import get_mandi_prices_report
from services.profit_service import list_farmer_profit_scenarios
from services.schemes_service import get_filtered_schemes
from services.soil_service import get_effective_soil_record
from services.weather_service import get_weather_and_flood_summary
from services.yield_service import predict_yield_and_harvest


async def build_dashboard_summary(db: Session, farmer: Farmer) -> dict:
    settings = get_settings()
    weather = await get_weather_and_flood_summary(farmer)
    latest_soil = get_effective_soil_record(db, farmer.id)
    active_crops = list_tracked_crops(db, farmer.id)
    recent_scans = list_disease_scans(db, farmer.id)[:5]
    profit_list = list_farmer_profit_scenarios(db, farmer.id)
    latest_profit = profit_list[0] if profit_list else None

    mandi = await get_mandi_prices_report(
        commodity=farmer.main_crops[0] if farmer.main_crops else None,
        state=farmer.state,
        district=farmer.district,
        include_demo=False,
    )

    yield_preview = None
    if active_crops:
        top_crop = active_crops[0]
        yield_preview = await predict_yield_and_harvest(
            db,
            farmer,
            YieldPredictRequest(
                crop_name=top_crop.crop_name,
                sowing_date=top_crop.sowing_date,
                acreage=top_crop.acreage,
                irrigation_type=top_crop.irrigation_type,
                growth_stage=top_crop.current_stage,
            ),
        )

    schemes_res = await get_filtered_schemes(
        state=farmer.state,
        category=farmer.farmer_category,
        crop=farmer.main_crops[0] if farmer.main_crops else None,
    )

    return {
        "farmer": farmer,
        "weather": weather,
        "latest_soil": latest_soil,
        "active_crops": active_crops,
        "recent_scans": recent_scans,
        "mandi_preview": mandi.records[:5],
        "yield_preview": yield_preview,
        "latest_profit": latest_profit,
        "suggested_schemes": schemes_res.schemes[:4],
        "integrations_summary": settings.integration_statuses(),
    }
