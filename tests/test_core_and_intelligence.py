"""End-to-end API tests across Core Agriculture, Intelligence, Security, and Voice modules."""

import io


def _get_auth_headers(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Kavitha Devi",
            "mobile": "9880011223",
            "password": "SafePassword123",
            "state": "Karnataka",
            "district": "Mandya",
            "village": "Srirangapatna",
            "farm_size_acres": 4.0,
            "main_crops": ["Ragi", "Tomato"],
            "preferred_language": "kn-IN",
            "gps_consent": True,
            "latitude": 12.42,
            "longitude": 76.68,
        },
    )
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_integrations_status_never_leaks_secrets(client):
    res = client.get("/api/v1/integrations/status")
    assert res.status_code == 200
    payload = res.json()["integrations"]
    assert payload["imd_weather"]["status"] == "not_configured"
    assert payload["plantix"]["status"] == "not_configured"
    assert payload["cwc_flood"]["status"] == "not_configured"


def test_soil_upload_validation_review_and_override(client):
    headers = _get_auth_headers(client)

    # Reject mismatched magic bytes
    bad_upload = client.post(
        "/api/v1/soil/upload",
        headers=headers,
        files={"file": ("fake.pdf", io.BytesIO(b"not-a-pdf"), "application/pdf")},
        data={"source_type": "soil_health_card"},
    )
    assert bad_upload.status_code == 400

    # Valid PNG header upload -> requires mandatory review
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    ok_upload = client.post(
        "/api/v1/soil/upload",
        headers=headers,
        files={"file": ("shc.png", io.BytesIO(png_bytes), "image/png")},
        data={"source_type": "soil_health_card"},
    )
    assert ok_upload.status_code == 201
    upload_data = ok_upload.json()
    assert upload_data["requires_review"] is True
    rec_id = upload_data["record"]["id"]
    assert upload_data["record"]["status"] == "pending_review"

    # Mandatory review & confirm
    review = client.put(
        f"/api/v1/soil/records/{rec_id}/review",
        headers=headers,
        json={"ph": 6.4, "nitrogen_kg_ha": 240.0, "phosphorus_kg_ha": 18.0, "potassium_kg_ha": 150.0},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "verified"
    assert review.json()["ph"] == 6.4


def test_weather_honesty_and_no_synthetic_alerts(client):
    headers = _get_auth_headers(client)
    res = client.get("/api/v1/weather", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["imd_status"] == "not_configured"
    assert body["warnings"] == []
    assert body["flood_status"] == "unavailable"


def test_crops_fertilizer_pest_yield_nutrition_mandi_profit_schemes_voice(client):
    headers = _get_auth_headers(client)

    # Crop recommendation includes horticulture
    crops = client.post(
        "/api/v1/crops/recommend",
        headers=headers,
        json={"season": "Kharif", "water_availability": "moderate", "include_horticulture": True},
    )
    assert crops.status_code == 200
    categories = {item["category"] for item in crops.json()["recommendations"]}
    assert "vegetable" in categories or "fruit" in categories

    # Pest detection image upload reports honest not_configured when keys missing
    jpg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    pest = client.post(
        "/api/v1/pests/analyze",
        headers=headers,
        files={"file": ("leaf.jpg", io.BytesIO(jpg_bytes), "image/jpeg")},
        data={"crop_name": "Tomato"},
    )
    assert pest.status_code == 201
    assert pest.json()["status"] == "not_configured"

    # Fertilizer recommendation
    fert = client.post(
        "/api/v1/fertilizer/recommend",
        headers=headers,
        json={"crop_name": "Tomato", "growth_stage": "basal", "farm_size_acres": 2.0},
    )
    assert fert.status_code == 200
    assert fert.json()["organic_plan"][0]["price_status"] == "unavailable"

    # Yield prediction
    yld = client.post(
        "/api/v1/yield/predict",
        headers=headers,
        json={
            "crop_name": "Ragi",
            "sowing_date": "2026-07-01",
            "acreage": 2.0,
            "irrigation_type": "drip",
            "growth_stage": "flowering",
        },
    )
    assert yld.status_code == 200
    assert yld.json()["google_agri_status"] == "not_configured"
    assert yld.json()["yield_min_qtl_total"] <= yld.json()["yield_expected_qtl_total"] <= yld.json()["yield_max_qtl_total"]

    # Nutrition
    nut = client.get("/api/v1/nutrition?query=ragi", headers=headers)
    assert nut.status_code == 200
    assert "no medical claims" in nut.json()["medical_disclaimer"].lower()

    # Mandi: default returns no fake data; include_demo=true labels DEMO DATA
    mandi_live = client.get("/api/v1/mandi?commodity=Tomato", headers=headers)
    assert mandi_live.status_code == 200
    assert mandi_live.json()["records"] == []
    assert mandi_live.json()["is_demo_data"] is False

    mandi_demo = client.get("/api/v1/mandi?commodity=Tomato&include_demo=true", headers=headers)
    assert mandi_demo.status_code == 200
    assert mandi_demo.json()["is_demo_data"] is True
    assert "DEMO DATA" in mandi_demo.json()["label"]

    # Profit calculator
    prof = client.post(
        "/api/v1/profit/calculate",
        headers=headers,
        json={
            "crop_name": "Tomato",
            "farm_size_acres": 2.0,
            "seed_cost": 4000,
            "fertilizer_cost": 8000,
            "labour_cost": 15000,
            "expected_yield_qtl_per_acre": 100,
            "expected_price_per_qtl": 1200,
            "save_scenario": True,
        },
    )
    assert prof.status_code == 200
    assert prof.json()["total_cost"] == 27000.0
    assert prof.json()["expected_revenue"] == 240000.0
    assert len(prof.json()["scenarios"]) == 3

    # Schemes
    schemes = client.get("/api/v1/schemes?state=Karnataka", headers=headers)
    assert schemes.status_code == 200
    assert len(schemes.json()["schemes"]) >= 2

    # Voice assistant asks for photo before diagnosing disease when no scan exists
    voice = client.post(
        "/api/v1/voice/turn",
        headers=headers,
        json={"text": "My leaves have yellow spot disease, what spray?", "language_code": "en-IN"},
    )
    assert voice.status_code == 200
    assert voice.json()["missing_data_prompt"] is not None
    assert voice.json()["context_used"]["location"]["district"] == "Mandya"

    # Dashboard aggregation
    dash = client.get("/api/v1/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["farmer"]["full_name"] == "Kavitha Devi"
