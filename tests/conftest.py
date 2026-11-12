"""Shared pytest fixtures using isolated temporary SQLite database and uploads directory."""

import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test_raithamitra.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-at-least-32-bytes-long-123456")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    # Ensure external keys are blank in unit tests to verify honest not_configured behavior
    for key in (
        "SARVAM_API_KEY",
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "IMD_API_KEY",
        "OPENWEATHER_API_KEY",
        "CWC_API_URL",
        "PLANTIX_API_KEY",
        "PLANTIX_BASE_URL",
        "VISION_MODEL_API_KEY",
        "GOOGLE_AGRI_API_KEY",
        "DATA_GOV_IN_API_KEY",
        "CEDA_API_KEY",
        "USDA_FDC_API_KEY",
        "FERTILIZER_PRICE_API_URL",
    ):
        monkeypatch.setenv(key, "")

    from config import get_settings
    get_settings.cache_clear()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import database
    import models  # noqa: F401
    from utils.rate_limit import rate_limiter

    rate_limiter.reset()

    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    database.Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from main import app

    app.dependency_overrides[database.get_db] = override_get_db
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
    test_engine.dispose()
    get_settings.cache_clear()
