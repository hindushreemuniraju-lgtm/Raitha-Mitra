"""Authentication, GPS opt-in consent, and per-farmer authorization isolation tests."""


def _register_farmer(client, mobile: str, name: str, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={
            "full_name": name,
            "mobile": mobile,
            "email": email,
            "password": "StrongPassword123",
            "state": "Karnataka",
            "district": "Mandya",
            "village": "Maddur",
            "farm_size_acres": 3.0,
            "main_crops": ["Ragi", "Tomato"],
            "preferred_language": "kn-IN",
            "gps_consent": False,
            "latitude": 12.52,
            "longitude": 76.89,
        },
    )


def test_register_login_and_opt_in_gps_enforcement(client):
    res_a = _register_farmer(client, "9876543210", "Farmer A", "farmer.a@example.com")
    assert res_a.status_code == 201
    body_a = res_a.json()
    assert body_a["farmer"]["gps_consent"] is False
    # Coordinates must be null when gps_consent is False
    assert body_a["farmer"]["latitude"] is None
    assert body_a["farmer"]["longitude"] is None

    # Duplicate mobile blocked
    dup = _register_farmer(client, "9876543210", "Dup Farmer", "dup@example.com")
    assert dup.status_code == 409

    # Login succeeds
    login_ok = client.post(
        "/api/v1/auth/login",
        json={"identifier": "9876543210", "password": "StrongPassword123"},
    )
    assert login_ok.status_code == 200
    assert "access_token" in login_ok.json()

    # Invalid password rejected
    login_bad = client.post(
        "/api/v1/auth/login",
        json={"identifier": "9876543210", "password": "WrongPassword"},
    )
    assert login_bad.status_code == 401


def test_cross_farmer_authorization_isolation(client):
    res_a = _register_farmer(client, "9876500001", "Farmer A", "a1@example.com")
    res_b = _register_farmer(client, "9876500002", "Farmer B", "b1@example.com")
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # Farmer A creates a tracked crop
    crop_res = client.post(
        "/api/v1/crops/monitoring",
        headers=headers_a,
        json={
            "crop_name": "Tomato",
            "category": "vegetable",
            "sowing_date": "2026-10-01",
            "acreage": 1.5,
            "irrigation_type": "drip",
        },
    )
    assert crop_res.status_code == 201
    crop_id = crop_res.json()["id"]

    # Farmer B cannot list, update, or delete Farmer A's crop
    assert client.get("/api/v1/crops/monitoring", headers=headers_b).json() == []
    assert (
        client.put(
            f"/api/v1/crops/monitoring/{crop_id}",
            headers=headers_b,
            json={"current_stage": "flowering"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/crops/monitoring/{crop_id}", headers=headers_b).status_code == 404

    # Farmer A creates a voice session
    voice_res = client.post(
        "/api/v1/voice/turn",
        headers=headers_a,
        json={"text": "ನನ್ನ ಟೊಮೆಟೊ ಬೆಳೆಗೆ ನೀರು ಯಾವಾಗ ಕೊಡಬೇಕು?", "language_code": "kn-IN"},
    )
    assert voice_res.status_code == 200
    session_id = voice_res.json()["session_id"]

    # Farmer B cannot read Farmer A's voice messages
    assert (
        client.get(f"/api/v1/voice/sessions/{session_id}/messages", headers=headers_b).status_code
        == 404
    )
