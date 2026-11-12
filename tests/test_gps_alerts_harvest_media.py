"""Comprehensive tests for live GPS/reverse geocoding, media previews & isolation, flood/rain classification, harvest maturity guard, notification deduplication, and Kannada voice Q&A."""

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

from pypdf import PdfWriter


def _tiny_png_bytes() -> bytes:
    # Valid 1x1 PNG bytes
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\xf8\xcf\xc0"
        b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _tiny_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _register_and_auth(client, mobile: str, name: str, email: str, lang: str = "kn-IN"):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": name,
            "mobile": mobile,
            "email": email,
            "password": "StrongPassword123",
            "state": "Karnataka",
            "district": "Mandya",
            "taluk": "Malavalli",
            "village": "Kirugavalu",
            "farm_size_acres": 2.5,
            "main_crops": ["Tomato", "Paddy"],
            "preferred_language": lang,
            "gps_consent": False,
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, res.json()["farmer"]


def test_live_gps_verify_reverse_geocode_and_manual_fallback(client, monkeypatch):
    headers, _farmer = _register_and_auth(client, "9880011223", "Ramesh Gowda", "ramesh@farm.local")

    # 1. Mock Nominatim reverse geocode cleanly
    mock_geo = {
        "status": "ok",
        "latitude": 12.423456,
        "longitude": 77.123456,
        "village": "Kirugavalu",
        "taluk": "Malavalli",
        "district": "Mandya",
        "state": "Karnataka",
        "display_name": "Kirugavalu, Malavalli, Mandya, Karnataka, India",
        "source": "OpenStreetMap Nominatim",
    }
    with patch(
        "routers.location.NominatimGeocodingAdapter.reverse_geocode",
        new=AsyncMock(return_value=mock_geo),
    ):
        rev = client.get("/api/v1/location/reverse?lat=12.423456&lon=77.123456", headers=headers)
        assert rev.status_code == 200
        assert rev.json()["village"] == "Kirugavalu"
        assert rev.json()["taluk"] == "Malavalli"
        assert rev.json()["district"] == "Mandya"

    # 2. Verify and persist GPS location with opt-in continuous flag
    saved = client.post(
        "/api/v1/location/verify",
        headers=headers,
        json={
            "latitude": 12.423456,
            "longitude": 77.123456,
            "gps_consent": True,
            "continuous_gps_opt_in": True,
            "state": "Karnataka",
            "district": "Mandya",
            "taluk": "Malavalli",
            "village": "Kirugavalu",
            "location_address": "Kirugavalu, Malavalli, Mandya, Karnataka",
            "location_source": "gps_corrected",
        },
    )
    assert saved.status_code == 200
    body = saved.json()
    assert body["gps_consent"] is True
    assert body["continuous_gps_opt_in"] is True
    assert body["latitude"] == 12.423456
    assert body["taluk"] == "Malavalli"
    assert body["location_source"] == "gps_corrected"

    # 3. Manual revocation of GPS clears coordinates & keeps manual location intact
    revoked = client.post(
        "/api/v1/location/verify",
        headers=headers,
        json={
            "latitude": 12.423456,
            "longitude": 77.123456,
            "gps_consent": False,
            "continuous_gps_opt_in": False,
            "state": "Karnataka",
            "district": "Mandya",
            "taluk": "Malavalli",
            "village": "Kirugavalu",
            "location_source": "manual",
        },
    )
    assert revoked.status_code == 200
    assert revoked.json()["latitude"] is None
    assert revoked.json()["longitude"] is None
    assert revoked.json()["continuous_gps_opt_in"] is False
    assert revoked.json()["village"] == "Kirugavalu"


def test_media_uploads_soil_pdf_image_crop_photo_profile_and_isolation(client):
    headers_a, _ = _register_and_auth(client, "9880022331", "Lakshmi A", "lakshmi.a@farm.local")
    headers_b, _ = _register_and_auth(client, "9880022332", "Mohan B", "mohan.b@farm.local")

    png_bytes = _tiny_png_bytes()
    pdf_bytes = _tiny_pdf_bytes()

    # 1. Farmer profile photograph upload & signed persistence
    avatar = client.post(
        "/api/v1/farmers/me/photo",
        headers=headers_a,
        files={"file": ("farmer-portrait.png", png_bytes, "image/png")},
    )
    assert avatar.status_code == 200
    avatar_url = avatar.json()["avatar_url"]
    assert avatar_url and avatar_url.startswith("/api/v1/files/")
    dl_avatar = client.get(avatar_url)
    assert dl_avatar.status_code == 200
    assert dl_avatar.content == png_bytes

    # 2. Soil PDF upload & signed PDF retrieval
    soil_pdf = client.post(
        "/api/v1/soil/upload",
        headers=headers_a,
        data={"source_type": "soil_health_card"},
        files={"file": ("soil-card.pdf", pdf_bytes, "application/pdf")},
    )
    assert soil_pdf.status_code == 201
    rec_pdf = soil_pdf.json()["record"]
    assert rec_pdf["file_kind"] == "pdf"
    assert rec_pdf["file_mime_type"] == "application/pdf"
    assert client.get(rec_pdf["file_url"]).content == pdf_bytes

    # 3. Soil image upload & persistence
    soil_img = client.post(
        "/api/v1/soil/upload",
        headers=headers_a,
        data={"source_type": "lab_report"},
        files={"file": ("lab-report.png", png_bytes, "image/png")},
    )
    assert soil_img.status_code == 201
    rec_img = soil_img.json()["record"]
    assert rec_img["file_kind"] == "image"
    assert client.get(rec_img["file_url"]).content == png_bytes

    # 4. Disease scan leaf image preview URL
    scan = client.post(
        "/api/v1/pests/analyze",
        headers=headers_a,
        data={"crop_name": "Tomato"},
        files={"file": ("tomato-leaf.png", png_bytes, "image/png")},
    )
    assert scan.status_code == 201
    assert scan.json()["image_url"]
    assert client.get(scan.json()["image_url"]).content == png_bytes

    # 5. Tracked Tomato crop + tomato field photo upload
    crop = client.post(
        "/api/v1/crops/monitoring",
        headers=headers_a,
        json={
            "crop_name": "Tomato",
            "variety": "Arka Rakshak",
            "category": "vegetable",
            "sowing_date": (date.today() - timedelta(days=80)).isoformat(),
            "acreage": 1.5,
            "irrigation_type": "drip",
        },
    )
    assert crop.status_code == 201
    crop_id = crop.json()["id"]
    crop_photo = client.post(
        f"/api/v1/crops/monitoring/{crop_id}/photo",
        headers=headers_a,
        files={"file": ("tomato-field.png", png_bytes, "image/png")},
    )
    assert crop_photo.status_code == 200
    photos = crop_photo.json()["photos"]
    assert len(photos) == 1
    assert client.get(photos[0]["url"]).content == png_bytes

    # 6. Cross-farmer authorization isolation on files & crop photo upload
    asset_path = photos[0]["url"].split("?")[0]
    unauth_file = client.get(asset_path)
    assert unauth_file.status_code == 401
    forbidden_file = client.get(asset_path, headers=headers_b)
    assert forbidden_file.status_code == 404

    forbidden_upload = client.post(
        f"/api/v1/crops/monitoring/{crop_id}/photo",
        headers=headers_b,
        files={"file": ("intruder.png", png_bytes, "image/png")},
    )
    assert forbidden_upload.status_code == 404


def test_harvest_protection_maturity_guard_and_flood_classification(client):
    import asyncio
    from models.farmer import Farmer
    from schemas.weather import (
        DailyForecastPoint,
        FloodAdvisory,
        WeatherFloodOut,
        WeatherForecastPoint,
    )
    from services.harvest_protection_service import evaluate_crop_harvest_protection
    from services.weather_service import classify_weather_and_flood_risks

    # Simulated heavy rainfall WITHOUT official CWC/KSNDMC flood advisories
    hourly_heavy_rain = [
        WeatherForecastPoint(
            timestamp=f"2026-11-13T{h:02d}:00",
            temp_c=24.0,
            humidity_pct=88.0,
            rain_mm=2.5 if h < 24 else 1.2,
            rain_probability_pct=90.0,
            wind_kmh=22.0,
            wind_gust_kmh=34.0,
            weather_code=65,
            condition="Heavy rain",
        )
        for h in range(48)
    ]
    daily_heavy_rain = [
        DailyForecastPoint(
            date=(date.today() + timedelta(days=1)).isoformat(),
            temp_max_c=27.0,
            temp_min_c=19.0,
            rain_sum_mm=62.0,
            rain_probability_pct=92.0,
            precipitation_hours=10.0,
            rain_intensity="heavy",
            wind_max_kmh=38.0,
            weather_code=65,
            condition="Heavy rain",
        )
    ]

    # Classify WITHOUT official flood warning -> MUST NOT emit official_flood_warning
    alerts_no_official = classify_weather_and_flood_risks(
        location_label="Kirugavalu, Mandya",
        imd_warnings=[],
        flood_advisories=[],
        hourly=hourly_heavy_rain,
        daily=daily_heavy_rain,
    )
    types_no_official = {a.alert_type for a in alerts_no_official}
    assert "official_flood_warning" not in types_no_official
    assert "heavy_rainfall_warning" in types_no_official
    assert "estimated_waterlogging_risk" in types_no_official
    assert all(not a.is_official for a in alerts_no_official)

    # Classify WITH official KSNDMC / CWC warning -> emits official_flood_warning
    alerts_official = classify_weather_and_flood_risks(
        location_label="Kirugavalu, Mandya",
        imd_warnings=[],
        flood_advisories=[
            FloodAdvisory(
                station="KRS Dam Outflow",
                river="Cauvery",
                level_m=37.5,
                danger_level_m=38.0,
                status="Flood Warning",
                source="CWC / KSNDMC",
            )
        ],
        hourly=hourly_heavy_rain,
        daily=daily_heavy_rain,
    )
    assert any(a.alert_type == "official_flood_warning" and a.is_official for a in alerts_official)

    weather_fixture = WeatherFloodOut(
        location_label="Kirugavalu, Mandya, Karnataka",
        imd_status="not_configured",
        imd_source_note="IMD offline in test",
        forecast_status="configured",
        forecast_source="Open-Meteo",
        flood_status="unavailable",
        flood_source_note="No CWC alert",
        freshness_label="Test fixture",
        warnings=[],
        forecast=hourly_heavy_rain,
        daily_forecast=daily_heavy_rain,
        flood_advisories=[],
        classified_alerts=alerts_no_official,
    )
    dummy_farmer = Farmer(
        full_name="Test Farmer",
        mobile="9880099887",
        password_hash="x",
        state="Karnataka",
        district="Mandya",
        taluk="Malavalli",
        village="Kirugavalu",
        main_crops=["Tomato"],
    )

    # Case A: Mature Tomato (88 days old) facing 62 mm rain -> harvest_now
    mature_res = asyncio.run(
        evaluate_crop_harvest_protection(
            farmer=dummy_farmer,
            crop_id=1,
            crop_name="Tomato",
            variety="Arka Rakshak",
            sowing_date=date.today() - timedelta(days=88),
            current_stage="maturity",
            weather=weather_fixture,
        )
    )
    assert mature_res.readiness_status in ("harvest_ready", "overdue")
    assert mature_res.action == "harvest_now"
    assert "ಟೊಮೇಟೊ" in mature_res.explanation_kn

    # Case B: Immature Tomato (25 days old) facing 62 mm rain -> MUST NOT tell farmer to harvest!
    immature_res = asyncio.run(
        evaluate_crop_harvest_protection(
            farmer=dummy_farmer,
            crop_id=2,
            crop_name="Tomato",
            variety="Arka Rakshak",
            sowing_date=date.today() - timedelta(days=25),
            current_stage="vegetative",
            weather=weather_fixture,
        )
    )
    assert immature_res.readiness_status == "immature"
    assert immature_res.action != "harvest_now"
    assert immature_res.action in ("wait_for_maturity", "protect_crop")
    assert "not harvest" in immature_res.explanation_en.lower() or "immature" in immature_res.explanation_en.lower()


def test_monitoring_deduplication_and_voice_weather_harvest_grounding(client):
    headers, farmer_dict = _register_and_auth(client, "9880055443", "Siddappa", "siddu@farm.local", lang="kn-IN")

    # Add mature tomato crop
    crop = client.post(
        "/api/v1/crops/monitoring",
        headers=headers,
        json={
            "crop_name": "Tomato",
            "category": "vegetable",
            "sowing_date": (date.today() - timedelta(days=85)).isoformat(),
            "acreage": 2.0,
            "irrigation_type": "drip",
        },
    )
    assert crop.status_code == 201
    # Update stage to maturity explicitly
    client.put(f"/api/v1/crops/monitoring/{crop.json()['id']}", headers=headers, json={"current_stage": "maturity"})

    # Trigger notification check twice on same mock heavy rainfall -> zero duplicates created on run 2
    from schemas.weather import DailyForecastPoint, WeatherFloodOut, WeatherForecastPoint
    from services.weather_service import classify_weather_and_flood_risks

    hourly = [
        WeatherForecastPoint(
            timestamp=f"2026-11-13T{h:02d}:00",
            temp_c=28.0,
            humidity_pct=86.0,
            rain_mm=1.6,
            rain_probability_pct=88.0,
            wind_kmh=42.0,
            condition="Heavy rain",
        )
        for h in range(48)
    ]
    daily = [
        DailyForecastPoint(
            date=(date.today() + timedelta(days=1)).isoformat(),
            temp_max_c=29.0,
            temp_min_c=20.0,
            rain_sum_mm=45.0,
            rain_probability_pct=88.0,
            rain_intensity="heavy",
            wind_max_kmh=42.0,
            condition="Heavy rain",
        )
    ]
    mock_weather = WeatherFloodOut(
        location_label="Kirugavalu, Mandya, Karnataka",
        imd_status="not_configured",
        imd_source_note="IMD not configured",
        forecast_status="configured",
        forecast_source="Open-Meteo",
        flood_status="unavailable",
        flood_source_note="No CWC station active",
        freshness_label="Live mock",
        warnings=[],
        forecast=hourly,
        daily_forecast=daily,
        flood_advisories=[],
        classified_alerts=classify_weather_and_flood_risks(
            location_label="Kirugavalu, Mandya, Karnataka",
            imd_warnings=[],
            flood_advisories=[],
            hourly=hourly,
            daily=daily,
        ),
    )

    with patch("services.monitoring_service.get_weather_and_flood_summary", new=AsyncMock(return_value=mock_weather)):
        r1 = client.post("/api/v1/notifications/check-now", headers=headers)
        assert r1.status_code == 200
        count1 = r1.json()["total_count"]
        assert count1 >= 3  # heavy_rainfall_alert, harvest_reminder, strong_wind_alert, irrigation_recommendation, pest risk

        r2 = client.post("/api/v1/notifications/check-now", headers=headers)
        assert r2.status_code == 200
        assert r2.json()["total_count"] == count1  # Deduplication prevented duplicate notifications!

    first_id = r1.json()["items"][0]["id"]
    mark_one = client.post(f"/api/v1/notifications/{first_id}/read", headers=headers)
    assert mark_one.status_code == 200
    assert mark_one.json()["is_read"] is True

    mark_all = client.post("/api/v1/notifications/read-all", headers=headers)
    assert mark_all.status_code == 200

    # Voice assistant Kannada & English Q&A grounded in live forecast + flood + tomato crop
    with (
        patch("services.voice_service.get_weather_and_flood_summary", new=AsyncMock(return_value=mock_weather)),
        patch("services.harvest_protection_service.get_weather_and_flood_summary", new=AsyncMock(return_value=mock_weather)),
    ):
        kn_turn = client.post(
            "/api/v1/voice/turn",
            headers=headers,
            json={
                "text": "ನಾಳೆ ಮಳೆಯಾಗುತ್ತದೆಯೇ? ನಾನು ಇಂದು ಟೊಮೇಟೊ ಕೊಯ್ಲು ಮಾಡಬೇಕೇ?",
                "language_code": "kn-IN",
            },
        )
        assert kn_turn.status_code == 200
        assert "45.0" in kn_turn.json()["reply_text"]
        assert "Tomato" in kn_turn.json()["reply_text"] or "ಟೊಮೇಟೊ" in kn_turn.json()["reply_text"]

        en_flood = client.post(
            "/api/v1/voice/turn",
            headers=headers,
            json={"text": "Is there a flood warning in my area?", "language_code": "en-IN"},
        )
        assert en_flood.status_code == 200
        assert "No official" in en_flood.json()["reply_text"]
