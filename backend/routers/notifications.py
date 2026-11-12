"""Smart notifications & scheduled weather/harvest monitoring endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models.farmer import Farmer
from schemas.notifications import MonitoringRunOut, NotificationListOut, NotificationOut
from services.monitoring_service import (
    list_farmer_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    run_monitoring_all_farmers,
    run_monitoring_for_farmer,
)
from utils.security import get_current_farmer

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications & Monitoring"])


@router.get("", response_model=NotificationListOut)
def get_my_notifications(
    limit: int = Query(default=50, ge=1, le=200),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_farmer_notifications(db, current_farmer.id, limit=limit)


@router.post("/check-now", response_model=NotificationListOut)
async def check_alerts_now(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Run weather, flood, and crop-stage harvest evaluation right now for the authenticated farmer."""
    await run_monitoring_for_farmer(db, current_farmer)
    return list_farmer_notifications(db, current_farmer.id, limit=50)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_one_read(
    notification_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return mark_notification_read(db, current_farmer.id, notification_id)


@router.post("/read-all")
def mark_all_read(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    count = mark_all_notifications_read(db, current_farmer.id)
    return {"marked_read": count}


@router.get("/cron", response_model=MonitoringRunOut)
async def vercel_cron_monitoring(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Scheduled background weather & harvest check invoked by Vercel Cron."""
    settings = get_settings()
    if settings.CRON_SECRET:
        expected = f"Bearer {settings.CRON_SECRET}"
        if authorization != expected:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron authorization.")
    return await run_monitoring_all_farmers(db, trigger="vercel_cron")
