"""Smart notifications & scheduled weather monitoring schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    farmer_id: int
    crop_id: Optional[int] = None
    category: str
    alert_type_label: str
    priority: str
    dedup_key: str
    title_en: str
    title_kn: str
    message_en: str
    message_kn: str
    crop_name: Optional[str] = None
    growth_stage: Optional[str] = None
    recommendation_en: Optional[str] = None
    recommendation_kn: Optional[str] = None
    source_name: str
    metadata_json: Dict[str, Any]
    is_read: bool
    read_at: Optional[str] = None
    created_at: str


class NotificationListOut(BaseModel):
    unread_count: int
    total_count: int
    items: List[NotificationOut]


class MonitoringRunOut(BaseModel):
    trigger: str
    farmers_checked: int
    notifications_created: int
    summary: str
    ran_at: str
