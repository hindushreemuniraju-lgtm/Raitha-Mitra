"""Soil Health Card OCR parsing, mandatory review, and dataset estimate precedence."""

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import re
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy.orm import Session

from integrations.soil_dataset import SoilDatasetAdapter
from models.farmer import Farmer
from models.soil import SoilRecord
from schemas.soil import SoilRecordOut, SoilRecordReviewRequest
from utils.file_storage import (
    SOIL_ALLOWED_EXTENSIONS,
    build_media_url,
    persist_media_asset,
    save_validated_upload,
)


_SOIL_FIELD_PATTERNS: Dict[str, re.Pattern[str]] = {
    "ph": re.compile(r"\bpH\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "nitrogen_kg_ha": re.compile(r"(?:available\s*)?(?:nitrogen|N)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "phosphorus_kg_ha": re.compile(r"(?:available\s*)?(?:phosphorus|P2O5|P)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "potassium_kg_ha": re.compile(r"(?:available\s*)?(?:potassium|K2O|K)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "organic_carbon_pct": re.compile(r"(?:organic\s*carbon|OC)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "ec_ds_m": re.compile(r"(?:electrical\s*conductivity|EC)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "sulphur_ppm": re.compile(r"(?:sulphur|sulfur|S)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)\s*(?:ppm|mg/kg)?", re.IGNORECASE),
    "zinc_ppm": re.compile(r"(?:zinc|Zn)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "boron_ppm": re.compile(r"(?:boron|B)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "iron_ppm": re.compile(r"(?:iron|Fe)\b\s*[:=\-]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
}


def parse_soil_text(text: str) -> Dict[str, Optional[float]]:
    """Extract numeric soil metrics from raw text without fabricating missing values."""
    extracted: Dict[str, Optional[float]] = {k: None for k in _SOIL_FIELD_PATTERNS}
    if not text:
        return extracted
    for field, pattern in _SOIL_FIELD_PATTERNS.items():
        match = pattern.search(text)
        if match:
            try:
                extracted[field] = round(float(match.group(1)), 3)
            except ValueError:
                extracted[field] = None
    return extracted


def _extract_text_from_file(path: Path, raw_bytes: bytes) -> Tuple[str, str, str]:
    """Extract text from PDF or run optional local OCR on images."""
    if path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(BytesIO(raw_bytes))
            text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if text:
                return text, "extracted_pdf", "Text extracted from PDF. Please review and confirm all values."
            return "", "scanned_pdf_review_required", "PDF appears scanned without embedded text. Please review and enter lab values."
        except Exception:
            return "", "pdf_parse_error", "Could not parse PDF text automatically. Please enter values manually on the review screen."

    # Image file: try rapidocr_onnxruntime or pytesseract if installed on host
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        ocr = RapidOCR()
        result, _ = ocr(str(path))
        if result:
            text = "\n".join(line[1] for line in result)
            return text, "extracted_ocr", "OCR extracted values from image. Please review and correct carefully."
    except Exception:
        pass

    try:
        import pytesseract  # type: ignore
        from PIL import Image

        text = pytesseract.image_to_string(Image.open(path)).strip()
        if text:
            return text, "extracted_ocr", "Tesseract OCR extracted text. Please review and correct carefully."
    except Exception:
        pass

    return (
        "",
        "manual_review_required",
        "Image saved securely, but local OCR engine (Tesseract/RapidOCR) is not installed on the server. Enter values from your card on the review screen.",
    )


async def upload_and_extract_soil_report(
    db: Session,
    farmer: Farmer,
    file: UploadFile,
    source_type: str,
) -> tuple[SoilRecord, str, str]:
    if source_type not in {"lab_report", "soil_health_card"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_type must be 'lab_report' or 'soil_health_card'.",
        )

    safe_name, saved_path, raw_bytes = await save_validated_upload(
        file, subdir="soil_cards", allowed_extensions=SOIL_ALLOWED_EXTENSIONS
    )
    orig_name = Path(file.filename or safe_name).name[:255]
    asset = persist_media_asset(
        db,
        farmer_id=farmer.id,
        category="soil_cards",
        safe_filename=safe_name,
        original_filename=orig_name,
        content=raw_bytes,
    )
    raw_text, ocr_status, ocr_note = _extract_text_from_file(saved_path, raw_bytes)
    parsed = parse_soil_text(raw_text)

    record = SoilRecord(
        farmer_id=farmer.id,
        source_type=source_type,
        dataset_name="Farmer Uploaded Lab / SHC",
        confidence_level="pending_review",
        status="pending_review",
        ph=parsed["ph"],
        nitrogen_kg_ha=parsed["nitrogen_kg_ha"],
        phosphorus_kg_ha=parsed["phosphorus_kg_ha"],
        potassium_kg_ha=parsed["potassium_kg_ha"],
        organic_carbon_pct=parsed["organic_carbon_pct"],
        ec_ds_m=parsed["ec_ds_m"],
        sulphur_ppm=parsed["sulphur_ppm"],
        zinc_ppm=parsed["zinc_ppm"],
        boron_ppm=parsed["boron_ppm"],
        iron_ppm=parsed["iron_ppm"],
        raw_ocr_text=raw_text or None,
        original_filename=orig_name,
        stored_filename=safe_name,
        media_asset_id=asset.id,
        file_mime_type=asset.content_type,
        tested_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, ocr_status, ocr_note


def review_and_confirm_soil_record(
    db: Session,
    farmer: Farmer,
    record_id: int,
    payload: SoilRecordReviewRequest,
) -> SoilRecord:
    record = (
        db.query(SoilRecord)
        .filter(SoilRecord.id == record_id, SoilRecord.farmer_id == farmer.id)
        .first()
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soil record not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    record.status = "verified"
    record.confidence_level = "high" if record.source_type != "dataset_estimate" else record.confidence_level
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_dataset_soil_estimate(
    db: Session,
    farmer: Farmer,
    latitude: float,
    longitude: float,
    dataset_preference: str = "auto",
) -> SoilRecord:
    adapter = SoilDatasetAdapter()
    lookup = adapter.lookup_by_coordinates(latitude, longitude, dataset_preference)
    if not lookup["configured"] or not lookup["values"]:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=lookup["note"],
        )

    vals = lookup["values"]
    record = SoilRecord(
        farmer_id=farmer.id,
        source_type="dataset_estimate",
        dataset_name=lookup["dataset_name"],
        confidence_level=lookup["confidence_level"],
        status="verified",
        ph=vals.get("ph"),
        nitrogen_kg_ha=vals.get("nitrogen_kg_ha"),
        phosphorus_kg_ha=vals.get("phosphorus_kg_ha"),
        potassium_kg_ha=vals.get("potassium_kg_ha"),
        organic_carbon_pct=vals.get("organic_carbon_pct"),
        ec_ds_m=vals.get("ec_ds_m"),
        review_notes=lookup["note"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_effective_soil_record(db: Session, farmer_id: int) -> Optional[SoilRecord]:
    """Lab reports & Soil Health Cards strictly override dataset estimates."""
    lab = (
        db.query(SoilRecord)
        .filter(
            SoilRecord.farmer_id == farmer_id,
            SoilRecord.source_type.in_(["lab_report", "soil_health_card"]),
            SoilRecord.status == "verified",
        )
        .order_by(SoilRecord.created_at.desc())
        .first()
    )
    if lab:
        return lab
    return (
        db.query(SoilRecord)
        .filter(SoilRecord.farmer_id == farmer_id)
        .order_by(SoilRecord.created_at.desc())
        .first()
    )


def list_farmer_soil_records(db: Session, farmer_id: int) -> list[SoilRecord]:
    return (
        db.query(SoilRecord)
        .filter(SoilRecord.farmer_id == farmer_id)
        .order_by(SoilRecord.created_at.desc())
        .all()
    )


def serialize_soil_record(record: SoilRecord) -> SoilRecordOut:
    """Serialize SoilRecord with clean signed file_url for image/PDF preview."""
    mime = record.file_mime_type or (
        "application/pdf"
        if (record.original_filename or "").lower().endswith(".pdf")
        else "image/png"
        if (record.original_filename or "").lower().endswith(".png")
        else "image/jpeg"
        if record.media_asset_id
        else None
    )
    kind = "pdf" if mime == "application/pdf" else ("image" if record.media_asset_id else None)
    return SoilRecordOut(
        id=record.id,
        farmer_id=record.farmer_id,
        source_type=record.source_type,
        dataset_name=record.dataset_name,
        confidence_level=record.confidence_level,
        status=record.status,
        ph=record.ph,
        nitrogen_kg_ha=record.nitrogen_kg_ha,
        phosphorus_kg_ha=record.phosphorus_kg_ha,
        potassium_kg_ha=record.potassium_kg_ha,
        organic_carbon_pct=record.organic_carbon_pct,
        ec_ds_m=record.ec_ds_m,
        sulphur_ppm=record.sulphur_ppm,
        zinc_ppm=record.zinc_ppm,
        boron_ppm=record.boron_ppm,
        iron_ppm=record.iron_ppm,
        raw_ocr_text=record.raw_ocr_text,
        original_filename=record.original_filename,
        file_url=build_media_url(record.media_asset_id, record.farmer_id),
        file_kind=kind,
        file_mime_type=mime,
        review_notes=record.review_notes,
        tested_at=record.tested_at,
        created_at=record.created_at,
    )
