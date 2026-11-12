"""Voice assistant schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VoiceTokenRequest(BaseModel):
    language_code: str = Field(default="kn-IN", max_length=16)
    session_id: Optional[int] = None


class VoiceTokenOut(BaseModel):
    livekit_configured: bool
    sarvam_configured: bool
    status: str
    livekit_url: Optional[str] = None
    room_name: str
    token: Optional[str] = None
    language_code: str
    note: str


class VoiceTurnRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language_code: str = Field(default="kn-IN", max_length=16)
    session_id: Optional[int] = None
    interrupted_previous: bool = False


class VoiceMessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    language_code: str
    content: str
    interrupted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VoiceSessionOut(BaseModel):
    id: int
    language_code: str
    room_name: Optional[str] = None
    channel: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VoiceTurnOut(BaseModel):
    session_id: int
    language_code: str
    recognized_text: str
    reply_text: str
    audio_base64: Optional[str] = None
    audio_mime: Optional[str] = None
    sarvam_status: str
    context_used: Dict[str, Any]
    missing_data_prompt: Optional[str] = None
    messages: List[VoiceMessageOut]
