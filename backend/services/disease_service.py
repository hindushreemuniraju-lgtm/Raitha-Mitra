"""Pest and disease diagnosis orchestration (Plantix primary + pluggable fallback)."""

from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from integrations.disease_vision_fallback import DiseaseVisionFallbackAdapter
from integrations.plantix import PlantixAdapter
from models.disease import DiseaseScan
from models.farmer import Farmer
from utils.file_storage import IMAGE_ALLOWED_EXTENSIONS, save_validated_upload


async def analyze_crop_disease_image(
    db: Session,
    farmer: Farmer,
    file: UploadFile,
    crop_name: Optional[str] = None,
) -> DiseaseScan:
    safe_name, saved_path, _ = await save_validated_upload(
        file, subdir="leaf_images", allowed_extensions=IMAGE_ALLOWED_EXTENSIONS
    )

    plantix = PlantixAdapter()
    fallback = DiseaseVisionFallbackAdapter()

    if plantix.is_configured:
        result = await plantix.analyze_image(
            saved_path,
            crop_name=crop_name,
            latitude=farmer.latitude if farmer.gps_consent else None,
            longitude=farmer.longitude if farmer.gps_consent else None,
            farmer_id=farmer.id,
        )
    elif fallback.is_configured:
        result = await fallback.analyze_image(saved_path, crop_name=crop_name)
    else:
        result = {
            "status": "not_configured",
            "adapter": "none_configured",
            "confidence": None,
            "diagnosis_name": None,
            "symptoms": [],
            "organic_treatments": [],
            "chemical_treatments": [],
            "precautions": [
                "Configure Plantix B2B credentials (PLANTIX_BASE_URL, PLANTIX_API_KEY) or a fallback vision model (VISION_MODEL_*)."
            ],
            "raw_summary": "Image saved safely, but neither Plantix nor a fallback vision model is configured.",
        }

    scan = DiseaseScan(
        farmer_id=farmer.id,
        crop_name=crop_name.strip() if crop_name else None,
        stored_filename=safe_name,
        adapter_used=str(result.get("adapter", "unknown")),
        confidence=result.get("confidence"),
        status=str(result.get("status", "not_configured")),
        diagnosis_name=result.get("diagnosis_name"),
        symptoms=list(result.get("symptoms") or []),
        organic_treatments=list(result.get("organic_treatments") or []),
        chemical_treatments=list(result.get("chemical_treatments") or []),
        precautions=list(result.get("precautions") or []),
        raw_summary=result.get("raw_summary"),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def list_disease_scans(db: Session, farmer_id: int) -> List[DiseaseScan]:
    return (
        db.query(DiseaseScan)
        .filter(DiseaseScan.farmer_id == farmer_id)
        .order_by(DiseaseScan.created_at.desc())
        .all()
    )
