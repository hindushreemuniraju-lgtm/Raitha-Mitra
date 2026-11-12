"""Safe file upload validation, persistent DB/disk media storage, and signed file access URLs."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional, Tuple
import uuid

from fastapi import HTTPException, UploadFile, status
import jwt
from sqlalchemy.orm import Session

from config import get_settings
from models.media import MediaAsset


SOIL_ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
IMAGE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

_EXT_TO_MIME = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
}


def _detect_magic_type(header: bytes) -> str:
    if header.startswith(b"%PDF"):
        return ".pdf"
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
        return ".webp"
    if len(header) >= 12 and header[4:8] == b"ftyp":
        return ".heic"
    return ""


async def save_validated_upload(
    upload: UploadFile,
    subdir: str,
    allowed_extensions: Iterable[str],
) -> Tuple[str, Path, bytes]:
    """Validate extension, magic signature, and max size, then save under a safe UUID name."""
    settings = get_settings()
    allowed = {ext.lower() for ext in allowed_extensions}

    original_name = Path(upload.filename or "upload").name
    ext = Path(original_name).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Allowed: {', '.join(sorted(allowed))}.",
        )

    content = await upload.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_MB} MB.",
        )

    detected = _detect_magic_type(content[:16])
    valid_magic = (
        (ext == ".pdf" and detected == ".pdf")
        or (ext in {".jpg", ".jpeg"} and detected == ".jpg")
        or (ext == ".png" and detected == ".png")
        or (ext == ".webp" and detected == ".webp")
        or (ext == ".heic" and detected == ".heic")
    )
    if not valid_magic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match the declared file extension.",
        )

    safe_subdir = Path(subdir).name
    target_dir = Path(settings.UPLOAD_DIR).resolve() / safe_subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    target_path = (target_dir / safe_filename).resolve()
    if target_dir not in target_path.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload path.",
        )

    target_path.write_bytes(content)
    return safe_filename, target_path, content


def persist_media_asset(
    db: Session,
    *,
    farmer_id: int,
    category: str,
    safe_filename: str,
    original_filename: str,
    content: bytes,
) -> MediaAsset:
    """Persist validated file bytes in the database so previews survive refreshes & serverless deploys."""
    ext = Path(safe_filename).suffix.lower()
    mime = _EXT_TO_MIME.get(ext, "application/octet-stream")
    file_kind = "pdf" if ext == ".pdf" else "image"
    asset = MediaAsset(
        id=uuid.uuid4().hex,
        farmer_id=farmer_id,
        category=category,
        stored_filename=safe_filename,
        original_filename=Path(original_filename or safe_filename).name[:240],
        content_type=mime,
        file_kind=file_kind,
        size_bytes=len(content),
        data=content,
    )
    db.add(asset)
    db.flush()
    return asset


def create_file_access_token(asset_id: str, farmer_id: int, ttl_minutes: int = 120) -> str:
    """Create a short-lived signed token scoped strictly to one asset and farmer."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "purpose": "media_view",
        "asset_id": asset_id,
        "farmer_id": farmer_id,
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_file_access_token(asset_id: str, token: str) -> Optional[int]:
    """Validate signed media token and return authorized farmer_id if valid."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "media_view" or payload.get("asset_id") != asset_id:
            return None
        return int(payload.get("farmer_id"))
    except Exception:
        return None


def build_media_url(asset_id: Optional[str], farmer_id: int) -> Optional[str]:
    """Return an authenticated API URL for rendering images/PDFs in the frontend (never a local path)."""
    if not asset_id:
        return None
    token = create_file_access_token(asset_id, farmer_id)
    return f"/api/v1/files/{asset_id}?token={token}"
