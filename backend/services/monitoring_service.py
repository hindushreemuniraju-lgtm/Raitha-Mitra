"""Scheduled weather, flood, and crop-stage harvest notification engine."""

from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.farmer import Farmer
from models.notification import MonitoringRunLog, Notification
from schemas.notifications import MonitoringRunOut, NotificationListOut, NotificationOut
from schemas.weather import WeatherFloodOut
from services.harvest_protection_service import get_farmer_harvest_protection
from services.weather_service import get_weather_and_flood_summary


def serialize_notification(n: Notification) -> NotificationOut:
    return NotificationOut(
        id=n.id,
        farmer_id=n.farmer_id,
        crop_id=n.crop_id,
        category=n.category,
        alert_type_label=n.alert_type_label,
        priority=n.priority,
        dedup_key=n.dedup_key,
        title_en=n.title_en,
        title_kn=n.title_kn,
        message_en=n.message_en,
        message_kn=n.message_kn,
        crop_name=n.crop_name,
        growth_stage=n.growth_stage,
        recommendation_en=n.recommendation_en,
        recommendation_kn=n.recommendation_kn,
        source_name=n.source_name,
        metadata_json=n.metadata_json or {},
        is_read=n.is_read,
        read_at=n.read_at.isoformat() if n.read_at else None,
        created_at=n.created_at.isoformat() if n.created_at else datetime.now(timezone.utc).isoformat(),
    )


def _create_if_new(
    db: Session,
    *,
    farmer_id: int,
    dedup_key: str,
    category: str,
    alert_type_label: str,
    priority: str,
    title_en: str,
    title_kn: str,
    message_en: str,
    message_kn: str,
    source_name: str,
    crop_id: Optional[int] = None,
    crop_name: Optional[str] = None,
    growth_stage: Optional[str] = None,
    recommendation_en: Optional[str] = None,
    recommendation_kn: Optional[str] = None,
    metadata_json: Optional[Dict] = None,
) -> Optional[Notification]:
    existing = (
        db.query(Notification)
        .filter(Notification.farmer_id == farmer_id, Notification.dedup_key == dedup_key)
        .first()
    )
    if existing:
        return None
    item = Notification(
        farmer_id=farmer_id,
        crop_id=crop_id,
        category=category,
        alert_type_label=alert_type_label,
        priority=priority,
        dedup_key=dedup_key,
        title_en=title_en,
        title_kn=title_kn,
        message_en=message_en,
        message_kn=message_kn,
        crop_name=crop_name,
        growth_stage=growth_stage,
        recommendation_en=recommendation_en,
        recommendation_kn=recommendation_kn,
        source_name=source_name,
        metadata_json=metadata_json or {},
        is_read=False,
    )
    db.add(item)
    return item


async def run_monitoring_for_farmer(
    db: Session,
    farmer: Farmer,
    *,
    weather_override: Optional[WeatherFloodOut] = None,
) -> List[Notification]:
    """Evaluate weather, flood, and crop stage protection and store deduplicated notifications."""
    today_key = date.today().isoformat()
    weather = weather_override or await get_weather_and_flood_summary(farmer)
    harvest_summary = await get_farmer_harvest_protection(db, farmer, weather_override=weather)

    created: List[Notification] = []
    hourly = weather.forecast or []
    daily = weather.daily_forecast or []

    next_48h_rain = round(sum(float(p.rain_mm or 0.0) for p in hourly[:48]), 1)
    max_rain_prob = round(max([float(p.rain_probability_pct or 0.0) for p in hourly[:48]] or [0.0]), 0)
    max_wind = round(max([float(p.wind_kmh or 0.0) for p in hourly[:48]] or [0.0]), 1)
    max_temp = round(max([float(d.temp_max_c) for d in daily[:2]] or [float(p.temp_c) for p in hourly[:24]] or [0.0]), 1)
    min_temp = round(min([float(d.temp_min_c) for d in daily[:2]] or [float(p.temp_c) for p in hourly[:24]] or [99.0]), 1)
    max_humidity = round(max([float(p.humidity_pct or 0.0) for p in hourly[:48]] or [0.0]), 0)
    location_tag = weather.location_label

    # 1. Official Flood Warning (ONLY if CWC / KSNDMC / IMD reported active official flood/release alert)
    for alert in weather.classified_alerts:
        if alert.alert_type == "official_flood_warning":
            n = _create_if_new(
                db,
                farmer_id=farmer.id,
                dedup_key=f"flood_warning:{today_key}:{farmer.district or farmer.state}",
                category="flood_warning",
                alert_type_label="official_flood_warning",
                priority="critical",
                title_en=alert.title_en,
                title_kn=alert.title_kn,
                message_en=alert.message_en,
                message_kn=alert.message_kn,
                recommendation_en="Move harvested produce and electrical pump equipment to higher ground.",
                recommendation_kn="ಕೊಯ್ಲು ಮಾಡಿದ ಬೆಳೆ ಮತ್ತು ಪಂಪ್ ಸೆಟ್‌ಗಳನ್ನು ಎತ್ತರದ ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ ಸ್ಥಳಾಂತರಿಸಿ.",
                source_name=alert.source,
                metadata_json={"location": location_tag, "is_official": True},
            )
            if n:
                created.append(n)

    # 2 & 3. Heavy Rainfall Warning / Rainfall Alert (crop-contextualized when harvest decisions exist)
    if next_48h_rain >= 30.0 or any(d.rain_sum_mm >= 35.0 for d in daily[:2]):
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"heavy_rainfall_alert:{today_key}:{location_tag}",
            category="heavy_rainfall_alert",
            alert_type_label="heavy_rainfall_warning",
            priority="high",
            title_en=f"Heavy Rainfall Alert for {location_tag} ({next_48h_rain:.0f} mm / 48h)",
            title_kn=f"{location_tag} ಪ್ರದೇಶಕ್ಕೆ ಭಾರೀ ಮಳೆ ಎಚ್ಚರಿಕೆ ({next_48h_rain:.0f} ಮಿ.ಮೀ / 48 ಗಂ)",
            message_en=(
                f"Forecast indicates up to {next_48h_rain:.1f} mm of rain in the next 48 hours (max probability {max_rain_prob:.0f}%). "
                "Open field drainage furrows, avoid fertilizer/pesticide spraying, and inspect mature crops."
            ),
            message_kn=(
                f"ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ {next_48h_rain:.1f} ಮಿ.ಮೀ ವರೆಗೆ ಭಾರೀ ಮಳೆ ಸಾಧ್ಯತೆ ಇದೆ ({max_rain_prob:.0f}% ಸಂಭವನೀಯತೆ). "
                "ಹೊಲದ ನೀರು ಬಸಿದುಹೋಗುವ ಕಾಲುವೆಗಳನ್ನು ತೆರೆಯಿರಿ ಮತ್ತು ಸಿಂಪಡಣೆ ಮುಂದೂಡಿ."
            ),
            recommendation_en="Ensure field drainage channels are open; delay foliar spray until rain clears.",
            recommendation_kn="ಹೊಲದ ಬಸಿಕಾಲುವೆಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ; ಮಳೆ ನಿಲ್ಲುವವರೆಗೆ ಸಿಂಪಡಣೆ ಮಾಡಬೇಡಿ.",
            source_name=weather.forecast_source or "Open-Meteo",
            metadata_json={"rain_48h_mm": next_48h_rain, "rain_prob_pct": max_rain_prob},
        )
        if n:
            created.append(n)
    elif next_48h_rain >= 8.0 or max_rain_prob >= 65.0:
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"rainfall_alert:{today_key}:{location_tag}",
            category="rainfall_alert",
            alert_type_label="general_weather_advisory",
            priority="medium",
            title_en=f"Rainfall Expected in {location_tag} ({next_48h_rain:.1f} mm)",
            title_kn=f"{location_tag} ಪ್ರದೇಶದಲ್ಲಿ ಮಳೆ ಸಾಧ್ಯತೆ ({next_48h_rain:.1f} ಮಿ.ಮೀ)",
            message_en=(
                f"Light to moderate rainfall (~{next_48h_rain:.1f} mm, {max_rain_prob:.0f}% chance) is forecast over the next 48 hours."
            ),
            message_kn=(
                f"ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ಸಾಧಾರಣ ಮಳೆ (~{next_48h_rain:.1f} ಮಿ.ಮೀ, {max_rain_prob:.0f}% ಸಾಧ್ಯತೆ) ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ."
            ),
            recommendation_en="Plan field spraying and irrigation around rainfall hours.",
            recommendation_kn="ಮಳೆ ಸಮಯವನ್ನು ಗಮನಿಸಿ ನೀರಾವರಿ ಮತ್ತು ಸಿಂಪಡಣೆ ಯೋಜಿಸಿ.",
            source_name=weather.forecast_source or "Open-Meteo",
            metadata_json={"rain_48h_mm": next_48h_rain, "rain_prob_pct": max_rain_prob},
        )
        if n:
            created.append(n)

    # 4. Crop-Specific Harvest Reminders & Immature Protection Alerts
    for dec in harvest_summary.decisions:
        if dec.action in ("harvest_now", "prepare_harvest", "delay_harvest", "protect_crop") and (
            dec.rain_72h_mm >= 12.0 or dec.readiness_status in ("harvest_ready", "overdue", "approaching_maturity")
        ):
            prio = "critical" if dec.action == "harvest_now" else ("high" if dec.rain_72h_mm >= 25.0 else "medium")
            n = _create_if_new(
                db,
                farmer_id=farmer.id,
                crop_id=dec.crop_id,
                dedup_key=f"harvest_reminder:{today_key}:{dec.crop_id or dec.crop_name}:{dec.action}",
                category="harvest_reminder",
                alert_type_label="heavy_rainfall_warning" if dec.rain_72h_mm >= 30.0 else "general_weather_advisory",
                priority=prio,
                title_en=dec.headline_en,
                title_kn=dec.headline_kn,
                message_en=dec.explanation_en,
                message_kn=dec.explanation_kn,
                crop_name=dec.crop_name,
                growth_stage=dec.current_stage,
                recommendation_en=dec.precautions_en[0] if dec.precautions_en else dec.action_label_en,
                recommendation_kn=dec.precautions_kn[0] if dec.precautions_kn else dec.action_label_kn,
                source_name="Raitha Mitra Harvest Protection Engine",
                metadata_json={
                    "action": dec.action,
                    "readiness_status": dec.readiness_status,
                    "days_remaining": dec.days_remaining_to_maturity,
                    "rain_72h_mm": dec.rain_72h_mm,
                },
            )
            if n:
                created.append(n)

    # 5. Pest & Disease Weather Risk (high humidity + rain + warm temperature)
    if max_humidity >= 82.0 and next_48h_rain >= 10.0 and harvest_summary.decisions:
        crops_text = ", ".join(sorted({d.crop_name for d in harvest_summary.decisions})[:3])
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"pest_disease_weather_risk:{today_key}:{location_tag}",
            category="pest_disease_weather_risk",
            alert_type_label="general_weather_advisory",
            priority="medium",
            title_en=f"Fungal & Blight Weather Risk ({max_humidity:.0f}% Humidity)",
            title_kn=f"ಶಿಲೀಂಧ್ರ ಮತ್ತು ಕೊಳೆ ರೋಗದ ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ ({max_humidity:.0f}% ತೇವಾಂಶ)",
            message_en=(
                f"High relative humidity ({max_humidity:.0f}%) combined with expected rain ({next_48h_rain:.1f} mm) increases fungal, blast, or blight pressure on {crops_text}."
            ),
            message_kn=(
                f"ಅಧಿಕ ತೇವಾಂಶ ({max_humidity:.0f}%) ಮತ್ತು ಮಳೆ ({next_48h_rain:.1f} ಮಿ.ಮೀ) ಕಾರಣದಿಂದ {crops_text} ಬೆಳೆಗಳಲ್ಲಿ ಶಿಲೀಂಧ್ರ/ಕೊಳೆ ರೋಗದ ಅಪಾಯ ಹೆಚ್ಚಿದೆ."
            ),
            crop_name=crops_text,
            recommendation_en="Inspect lower leaves after rain and upload a leaf scan in Pest & Disease if spots appear.",
            recommendation_kn="ಮಳೆ ನಂತರ ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ; ಕಲೆಗಳು ಕಂಡರೆ ಕೀಟ-ರೋಗ ಸ್ಕ್ಯಾನ್ ಬಳಸಿ.",
            source_name="Weather-Disease Risk Engine",
            metadata_json={"max_humidity_pct": max_humidity, "rain_48h_mm": next_48h_rain},
        )
        if n:
            created.append(n)

    # 6. Irrigation Recommendation (skip irrigation ahead of significant rain)
    if next_48h_rain >= 15.0 or max_rain_prob >= 70.0:
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"irrigation_recommendation:{today_key}:{location_tag}",
            category="irrigation_recommendation",
            alert_type_label="general_weather_advisory",
            priority="low",
            title_en="Skip Scheduled Irrigation — Rain Forecast",
            title_kn="ಮಳೆ ಮುನ್ಸೂಚನೆ: ನೀರಾವರಿ ತಾತ್ಕಾಲಿಕವಾಗಿ ನಿಲ್ಲಿಸಿ",
            message_en=(
                f"With ~{next_48h_rain:.1f} mm rainfall ({max_rain_prob:.0f}% chance) expected over 48 hours in {location_tag}, pause irrigation to save water/power and prevent root waterlogging."
            ),
            message_kn=(
                f"{location_tag} ಪ್ರದೇಶದಲ್ಲಿ ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ~{next_48h_rain:.1f} ಮಿ.ಮೀ ಮಳೆ ({max_rain_prob:.0f}%) ನಿರೀಕ್ಷೆಯಿರುವುದರಿಂದ ನೀರಾವರಿಯನ್ನು ತಾತ್ಕಾಲಿಕವಾಗಿ ಮುಂದೂಡಿ."
            ),
            recommendation_en="Pause drip/flood irrigation for 24-48 hours and re-check soil moisture afterwards.",
            recommendation_kn="24-48 ಗಂಟೆಗಳ ಕಾಲ ನೀರಾವರಿ ನಿಲ್ಲಿಸಿ ನಂತರ ಮಣ್ಣಿನ ತೇವಾಂಶ ಪರಿಶೀಲಿಸಿ.",
            source_name="Irrigation Weather Advisor",
            metadata_json={"rain_48h_mm": next_48h_rain},
        )
        if n:
            created.append(n)

    # 7. Strong Wind Alert
    if max_wind >= 35.0:
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"strong_wind_alert:{today_key}:{location_tag}",
            category="strong_wind_alert",
            alert_type_label="general_weather_advisory",
            priority="high" if max_wind >= 50.0 else "medium",
            title_en=f"Strong Wind Advisory ({max_wind:.0f} km/h)",
            title_kn=f"ಬಲವಾದ ಗಾಳಿ ಎಚ್ಚರಿಕೆ ({max_wind:.0f} ಕಿ.ಮೀ/ಗಂ)",
            message_en=(
                f"Winds up to {max_wind:.0f} km/h are expected in {location_tag}. Secure banana/tomato stakes, shade nets, and postpone spraying."
            ),
            message_kn=(
                f"{location_tag} ಪ್ರದೇಶದಲ್ಲಿ ಗಂಟೆಗೆ {max_wind:.0f} ಕಿ.ಮೀ ವೇಗದ ಗಾಳಿ ಬೀಸುವ ಸಾಧ್ಯತೆಯಿದೆ. ಬಾಳೆ/ಟೊಮೇಟೊ ಆಧಾರ ಕಂಬಗಳನ್ನು ಭದ್ರಪಡಿಸಿ."
            ),
            recommendation_en="Reinforce staking poles and avoid spray drift during windy hours.",
            recommendation_kn="ಆಧಾರ ಕಂಬಗಳನ್ನು ಭದ್ರಪಡಿಸಿ ಮತ್ತು ಗಾಳಿಯ ಸಮಯದಲ್ಲಿ ಸಿಂಪಡಣೆ ಮಾಡಬೇಡಿ.",
            source_name=weather.forecast_source or "Open-Meteo",
            metadata_json={"max_wind_kmh": max_wind},
        )
        if n:
            created.append(n)

    # 8. Extreme Temperature Alert (Heat stress >= 39C or Cold stress <= 10C)
    if max_temp >= 39.0:
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"extreme_temperature_alert:{today_key}:heat:{location_tag}",
            category="extreme_temperature_alert",
            alert_type_label="general_weather_advisory",
            priority="high",
            title_en=f"High Heat Stress Alert ({max_temp:.1f}°C)",
            title_kn=f"ತೀವ್ರ ಬಿಸಿಲು / ಶಾಖ ಎಚ್ಚರಿಕೆ ({max_temp:.1f}°C)",
            message_en=(
                f"Daytime temperature may reach {max_temp:.1f}°C in {location_tag}. Irrigate during cool morning/evening hours and apply crop residue mulching."
            ),
            message_kn=(
                f"{location_tag} ಪ್ರದೇಶದಲ್ಲಿ ಗರಿಷ್ಠ ತಾಪಮಾನ {max_temp:.1f}°C ತಲುಪಬಹುದು. ಬೆಳಿಗ್ಗೆ/ಸಂಜೆ ನೀರಾವರಿ ನೀಡಿ ಮತ್ತು ಮಲ್ಚಿಂಗ್ ಬಳಸಿ."
            ),
            recommendation_en="Harvest perishables early morning and provide light evening irrigation.",
            recommendation_kn="ಹಣ್ಣು-ತರಕಾರಿಗಳನ್ನು ಬೆಳಿಗ್ಗೆ ಬೇಗ ಕೊಯ್ಲು ಮಾಡಿ ಮತ್ತು ಸಂಜೆ ಹಗುರ ನೀರಾವರಿ ನೀಡಿ.",
            source_name=weather.forecast_source or "Open-Meteo",
            metadata_json={"max_temp_c": max_temp},
        )
        if n:
            created.append(n)
    elif min_temp <= 10.0 and min_temp > -20.0:
        n = _create_if_new(
            db,
            farmer_id=farmer.id,
            dedup_key=f"extreme_temperature_alert:{today_key}:cold:{location_tag}",
            category="extreme_temperature_alert",
            alert_type_label="general_weather_advisory",
            priority="medium",
            title_en=f"Low Night Temperature Alert ({min_temp:.1f}°C)",
            title_kn=f"ರಾತ್ರಿ ಕಡಿಮೆ ತಾಪಮಾನ ಎಚ್ಚರಿಕೆ ({min_temp:.1f}°C)",
            message_en=f"Minimum night temperature may drop to {min_temp:.1f}°C. Protect tender nurseries and cold-sensitive crops.",
            message_kn=f"ರಾತ್ರಿ ಕನಿಷ್ಠ ತಾಪಮಾನ {min_temp:.1f}°C ಗೆ ಇಳಿಯಬಹುದು. ಎಳೆಯ ಸಸಿಗಳನ್ನು ರಕ್ಷಿಸಿ.",
            source_name=weather.forecast_source or "Open-Meteo",
            metadata_json={"min_temp_c": min_temp},
        )
        if n:
            created.append(n)

    if created:
        db.commit()
        for item in created:
            db.refresh(item)
    return created


async def run_monitoring_all_farmers(db: Session, *, trigger: str = "scheduler") -> MonitoringRunOut:
    farmers = db.query(Farmer).all()
    total_created = 0
    for farmer in farmers:
        try:
            created = await run_monitoring_for_farmer(db, farmer)
            total_created += len(created)
        except Exception:
            # Never halt monitoring loop for remaining farmers if one lookup fails
            db.rollback()
            continue

    log = MonitoringRunLog(
        trigger=trigger,
        farmers_checked=len(farmers),
        notifications_created=total_created,
        summary=f"Checked {len(farmers)} farmer profiles; created {total_created} new alerts.",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return MonitoringRunOut(
        trigger=log.trigger,
        farmers_checked=log.farmers_checked,
        notifications_created=log.notifications_created,
        summary=log.summary or "",
        ran_at=log.ran_at.isoformat() if log.ran_at else datetime.now(timezone.utc).isoformat(),
    )


def list_farmer_notifications(db: Session, farmer_id: int, limit: int = 50) -> NotificationListOut:
    rows = (
        db.query(Notification)
        .filter(Notification.farmer_id == farmer_id)
        .order_by(Notification.is_read.asc(), Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )
    unread_count = (
        db.query(Notification)
        .filter(Notification.farmer_id == farmer_id, Notification.is_read.is_(False))
        .count()
    )
    total_count = db.query(Notification).filter(Notification.farmer_id == farmer_id).count()
    return NotificationListOut(
        unread_count=unread_count,
        total_count=total_count,
        items=[serialize_notification(r) for r in rows],
    )


def mark_notification_read(db: Session, farmer_id: int, notification_id: int) -> NotificationOut:
    row = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.farmer_id == farmer_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    if not row.is_read:
        row.is_read = True
        row.read_at = datetime.now(timezone.utc)
        db.add(row)
        db.commit()
        db.refresh(row)
    return serialize_notification(row)


def mark_all_notifications_read(db: Session, farmer_id: int) -> int:
    now = datetime.now(timezone.utc)
    updated = (
        db.query(Notification)
        .filter(Notification.farmer_id == farmer_id, Notification.is_read.is_(False))
        .update({Notification.is_read: True, Notification.read_at: now}, synchronize_session=False)
    )
    db.commit()
    return int(updated)
