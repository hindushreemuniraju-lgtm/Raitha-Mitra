"""Authenticated & signed file serving endpoints for uploaded images and PDFs."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models.media import MediaAsset
from utils.file_storage import verify_file_access_token


router = APIRouter(prefix="/api/v1/files", tags=["Media Files"])
optional_bearer = HTTPBearer(auto_error=False)


def _resolve_authorized_farmer_id(
    asset_id: str,
    token: Optional[str],
    credentials: Optional[HTTPAuthorizationCredentials],
) -> int:
    if token:
        farmer_id = verify_file_access_token(asset_id, token)
        if farmer_id is not None:
            return farmer_id

    if credentials is not None:
        settings = get_settings()
        try:
            payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
            sub = payload.get("sub")
            if sub is not None:
                return int(sub)
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication or valid file token required.",
    )


@router.get("/{asset_id}")
def serve_media_asset(
    asset_id: str,
    token: Optional[str] = Query(default=None),
    download: bool = Query(default=False),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: Session = Depends(get_db),
):
    farmer_id = _resolve_authorized_farmer_id(asset_id, token, credentials)

    asset = (
        db.query(MediaAsset)
        .filter(MediaAsset.id == asset_id, MediaAsset.farmer_id == farmer_id)
        .first()
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    content = asset.data
    if not content:
        settings = get_settings()
        disk_path = Path(settings.UPLOAD_DIR).resolve() / Path(asset.category).name / Path(asset.stored_filename).name
        if disk_path.exists():
            content = disk_path.read_bytes()

    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File payload unavailable.")

    disposition = "attachment" if download else "inline"
    safe_name = Path(asset.original_filename or asset.stored_filename).name.replace('"', "")
    headers = {
        "Content-Disposition": f'{disposition}; filename="{safe_name}"',
        "Cache-Control": "private, max-age=3600",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=content, media_type=asset.content_type, headers=headers)
