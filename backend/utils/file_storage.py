"""Safe file upload validation (extension, magic bytes, size limit, isolated storage)."""

from pathlib import Path
from typing import Iterable, Tuple
import uuid

from fastapi import HTTPException, UploadFile, status

from config import get_settings


SOIL_ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
IMAGE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


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
    target_dir = (Path(settings.UPLOAD_DIR).resolve() / safe_subdir)
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
