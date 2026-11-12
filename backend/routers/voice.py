"""Multilingual voice assistant endpoints (LiveKit tokens, audio/text turns, history)."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from integrations.voice_sarvam import SarvamAiAdapter
from models.farmer import Farmer
from schemas.voice import (
    VoiceMessageOut,
    VoiceSessionOut,
    VoiceTokenOut,
    VoiceTokenRequest,
    VoiceTurnOut,
    VoiceTurnRequest,
)
from services.voice_service import (
    issue_livekit_voice_token,
    list_session_messages,
    list_voice_sessions,
    process_voice_turn,
)
from utils.rate_limit import rate_limit
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/voice", tags=["Voice Assistant"])


@router.get("/sessions", response_model=List[VoiceSessionOut])
def get_sessions(
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_voice_sessions(db, current_farmer.id)


@router.get("/sessions/{session_id}/messages", response_model=List[VoiceMessageOut])
def get_messages(
    session_id: int,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return list_session_messages(db, current_farmer.id, session_id)


@router.post(
    "/token",
    response_model=VoiceTokenOut,
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
def create_voice_token(
    payload: VoiceTokenRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return issue_livekit_voice_token(db, current_farmer, payload.language_code, payload.session_id)


@router.post(
    "/turn",
    response_model=VoiceTurnOut,
    dependencies=[Depends(rate_limit(max_requests=40, window_seconds=60))],
)
async def voice_text_turn(
    payload: VoiceTurnRequest,
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    return await process_voice_turn(
        db,
        current_farmer,
        text=payload.text,
        language_code=payload.language_code,
        session_id=payload.session_id,
        interrupted_previous=payload.interrupted_previous,
    )


@router.post(
    "/audio-turn",
    response_model=VoiceTurnOut,
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60))],
)
async def voice_audio_turn(
    audio: UploadFile = File(...),
    language_code: str = Form(default="kn-IN"),
    session_id: Optional[int] = Form(default=None),
    interrupted_previous: bool = Form(default=False),
    current_farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    raw_audio = await audio.read()
    if not raw_audio or len(raw_audio) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio clip is empty or exceeds maximum upload size.",
        )

    sarvam = SarvamAiAdapter()
    if not sarvam.is_configured:
        return await process_voice_turn(
            db,
            current_farmer,
            text="[Audio clip submitted while SARVAM_API_KEY is not configured]",
            language_code=language_code,
            session_id=session_id,
            interrupted_previous=interrupted_previous,
        )

    stt_res = await sarvam.transcribe_audio(
        raw_audio, audio.filename or "utterance.webm", language_code
    )
    transcript = stt_res.get("transcript") or ""
    if not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=stt_res.get("note") or "Could not recognize speech from audio. Please try speaking closer to the mic.",
        )

    return await process_voice_turn(
        db,
        current_farmer,
        text=transcript,
        language_code=language_code,
        session_id=session_id,
        interrupted_previous=interrupted_previous,
    )
