"""Multilingual voice assistant context builder, LiveKit token issuer, and conversation engine."""

import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config import get_settings
from integrations.voice_sarvam import LANGUAGE_NAMES, SarvamAiAdapter
from models.farmer import Farmer
from models.voice import VoiceMessage, VoiceSession
from schemas.voice import VoiceTokenOut, VoiceTurnOut
from services.crop_service import list_tracked_crops
from services.disease_service import list_disease_scans
from services.soil_service import get_effective_soil_record


_DISEASE_KEYWORDS = (
    "spot",
    "blight",
    "wilt",
    "rot",
    "pest",
    "insect",
    "worm",
    "yellow",
    "curl",
    "disease",
    "fungus",
    "ರೋಗ",
    "ಕೀಟ",
    "ಎಲೆ",
    "रोग",
    "कीट",
    "पत्ता",
    "తెగులు",
    "పురుగు",
)

_MISSING_PHOTO_PROMPTS: Dict[str, str] = {
    "kn-IN": "ನಿಮ್ಮ ಬೆಳೆಯ ರೋಗವನ್ನು ಖಚಿತಪಡಿಸಲು ದಯವಿಟ್ಟು ಬಾಧಿತ ಎಲೆ ಅಥವಾ ಕಾಂಡದ ಸ್ಪಷ್ಟ ಫೋಟೋವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ (Pest & Disease ಪುಟ ಬಳಸಿ).",
    "hi-IN": "फसल की बीमारी की सही पहचान के लिए कृपया प्रभावित पत्ती या पौधे की स्पष्ट फोटो अपलोड करें (कीट और रोग टैब देखें)।",
    "te-IN": "మీ పంట వ్యాధిని ఖచ్చితంగా గుర్తించడానికి దయచేసి ప్రభావిత ఆకు లేదా మొక్క యొక్క స్పష్టమైన ఫోటోను అప్‌లోడ్ చేయండి.",
    "ta-IN": "பயிர் நோயை துல்லியமாக கண்டறிய பாதிக்கப்பட்ட இலையின் தெளிவான புகைப்படத்தை பதிவேற்றவும்.",
    "mr-IN": "पिकावरील रोगाची अचूक तपासणी करण्यासाठी कृपया प्रभावित पानाचा स्पष्ट फोटो अपलोड करा.",
    "en-IN": "Before diagnosing a pest or disease, please upload a clear close-up photo of the affected leaf or plant in Pest & Disease Detection.",
}

_NOT_CONFIGURED_REPLIES: Dict[str, str] = {
    "kn-IN": "ಕ್ಷಮಿಸಿ, Sarvam AI ಧ್ವನಿ/ಚಾಟ್ API ಕೀ (SARVAM_API_KEY) ಕಾನ್ಫಿಗರ್ ಆಗಿಲ್ಲ. ನಿಮ್ಮ ಪ್ರೊಫೈಲ್ ಡೇಟಾ ಸಿದ್ಧವಾಗಿದೆ; ಲೈವ್ ಧ್ವನಿ ಉತ್ತರಕ್ಕಾಗಿ ದಯವಿಟ್ಟು backend/.env ನಲ್ಲಿ SARVAM_API_KEY ಸೇರಿಸಿ.",
    "hi-IN": "क्षमा करें, Sarvam AI API कुंजी (SARVAM_API_KEY) कॉन्फ़िगर नहीं है। आपका फ़ार्म संदर्भ तैयार है; लाइव उत्तर के लिए कृपया backend/.env में SARVAM_API_KEY जोड़ें।",
    "te-IN": "క్షమించండి, Sarvam AI API కీ (SARVAM_API_KEY) కాన్ఫిగర్ చేయబడలేదు. మీ ఫారమ్ సందర్భం సిద్ధంగా ఉంది; లైవ్ సమాధానాల కోసం backend/.env లో SARVAM_API_KEY జోడించండి.",
    "ta-IN": "மன்னிக்கவும், Sarvam AI API விசை (SARVAM_API_KEY) அமைக்கப்படவில்லை. நேரடி பதிலுக்கு backend/.env இல் SARVAM_API_KEY ஐ சேர்க்கவும்.",
    "mr-IN": "क्षमस्व, Sarvam AI API की (SARVAM_API_KEY) कॉन्फिगर केलेली नाही. थेट उत्तरांसाठी कृपया backend/.env मध्ये SARVAM_API_KEY जोडा.",
    "en-IN": "Sarvam AI (SARVAM_API_KEY) is not configured in backend/.env. Your farm context was loaded, and Raitha Mitra does not fabricate AI answers without a configured provider.",
}


def build_farmer_voice_context(db: Session, farmer: Farmer) -> Dict[str, Any]:
    """Gather grounded real farmer context (profile, soil, active crops, recent scans)."""
    soil = get_effective_soil_record(db, farmer.id)
    crops = list_tracked_crops(db, farmer.id)
    scans = list_disease_scans(db, farmer.id)

    soil_ctx: Optional[Dict[str, Any]] = None
    if soil:
        soil_ctx = {
            "source_type": soil.source_type,
            "status": soil.status,
            "confidence": soil.confidence_level,
            "ph": soil.ph,
            "nitrogen_kg_ha": soil.nitrogen_kg_ha,
            "phosphorus_kg_ha": soil.phosphorus_kg_ha,
            "potassium_kg_ha": soil.potassium_kg_ha,
            "organic_carbon_pct": soil.organic_carbon_pct,
        }

    return {
        "farmer_name": farmer.full_name,
        "location": {
            "state": farmer.state,
            "district": farmer.district,
            "village": farmer.village,
        },
        "farm_size_acres": farmer.farm_size_acres,
        "soil_type": farmer.soil_type,
        "main_crops": farmer.main_crops,
        "preferred_language": farmer.preferred_language,
        "soil_health": soil_ctx,
        "active_crops": [
            {
                "crop_name": c.crop_name,
                "stage": c.current_stage,
                "days_since_sowing": c.days_since_sowing,
                "acreage": c.acreage,
                "irrigation": c.irrigation_type,
            }
            for c in crops[:5]
        ],
        "recent_disease_scans": [
            {
                "crop_name": s.crop_name,
                "status": s.status,
                "diagnosis": s.diagnosis_name,
                "confidence": s.confidence,
            }
            for s in scans[:3]
        ],
    }


def _build_system_prompt(language_code: str, context: Dict[str, Any]) -> str:
    lang_label = LANGUAGE_NAMES.get(language_code, language_code)
    return (
        "You are Raitha Mitra ('Your Smart Farming Companion'), an AI agricultural advisor for Indian farmers.\n"
        f"STRICT LANGUAGE RULE: You MUST reply ONLY in {lang_label} (locale {language_code}) using natural, simple farmer-friendly language. Never switch to English unless en-IN is selected.\n"
        "STRICT GROUNDING RULE: Use the farmer context JSON below. NEVER ask the farmer for their crop, village, district, state, or farm size if already provided in the context.\n"
        "MISSING DATA RULE: If the farmer asks to diagnose a plant disease or pest without an uploaded photo/scan in recent_disease_scans, ask them to upload a clear leaf photo first rather than guessing.\n"
        "HONESTY RULE: Never invent weather alerts, mandi prices, or medical claims.\n"
        f"FARMER CONTEXT JSON:\n{json.dumps(context, ensure_ascii=False)}"
    )


def _get_or_create_session(
    db: Session, farmer: Farmer, language_code: str, session_id: Optional[int], channel: str
) -> VoiceSession:
    if session_id is not None:
        session = (
            db.query(VoiceSession)
            .filter(VoiceSession.id == session_id, VoiceSession.farmer_id == farmer.id)
            .first()
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice session not found.")
        session.language_code = language_code
        db.add(session)
        db.commit()
        return session

    room_name = f"raithamitra-f{farmer.id}-{uuid.uuid4().hex[:8]}"
    session = VoiceSession(
        farmer_id=farmer.id,
        language_code=language_code,
        room_name=room_name,
        channel=channel,
        title=f"Voice ({language_code})",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def issue_livekit_voice_token(
    db: Session, farmer: Farmer, language_code: str, session_id: Optional[int] = None
) -> VoiceTokenOut:
    settings = get_settings()
    session = _get_or_create_session(db, farmer, language_code, session_id, channel="livekit")
    lk_ok = bool(settings.LIVEKIT_URL and settings.LIVEKIT_API_KEY and settings.LIVEKIT_API_SECRET)
    sarvam_ok = bool(settings.SARVAM_API_KEY)

    if not lk_ok:
        return VoiceTokenOut(
            livekit_configured=False,
            sarvam_configured=sarvam_ok,
            status="not_configured",
            livekit_url=None,
            room_name=session.room_name or "",
            token=None,
            language_code=language_code,
            note="LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET not configured in backend/.env.",
        )

    from livekit import api as lk_api  # type: ignore

    context = build_farmer_voice_context(db, farmer)
    grant = lk_api.VideoGrants(room_join=True, room=session.room_name)
    token = (
        lk_api.AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
        .with_identity(f"farmer_{farmer.id}")
        .with_name(farmer.full_name)
        .with_metadata(json.dumps({"language_code": language_code, "context": context}, ensure_ascii=False))
        .with_grants(grant)
        .to_jwt()
    )

    return VoiceTokenOut(
        livekit_configured=True,
        sarvam_configured=sarvam_ok,
        status="ready",
        livekit_url=settings.LIVEKIT_URL,
        room_name=session.room_name or "",
        token=token,
        language_code=language_code,
        note="LiveKit room token issued with grounded farmer context.",
    )


async def process_voice_turn(
    db: Session,
    farmer: Farmer,
    *,
    text: str,
    language_code: str,
    session_id: Optional[int] = None,
    interrupted_previous: bool = False,
) -> VoiceTurnOut:
    session = _get_or_create_session(db, farmer, language_code, session_id, channel="hybrid")
    context = build_farmer_voice_context(db, farmer)

    if interrupted_previous:
        last_assistant = (
            db.query(VoiceMessage)
            .filter(
                VoiceMessage.session_id == session.id,
                VoiceMessage.farmer_id == farmer.id,
                VoiceMessage.role == "assistant",
            )
            .order_by(VoiceMessage.id.desc())
            .first()
        )
        if last_assistant:
            last_assistant.interrupted = True
            db.add(last_assistant)

    farmer_msg = VoiceMessage(
        session_id=session.id,
        farmer_id=farmer.id,
        role="farmer",
        language_code=language_code,
        content=text.strip(),
        context_snapshot=context,
    )
    db.add(farmer_msg)
    db.commit()

    # Check if farmer is asking for a disease diagnosis without any scanned leaf photo
    lowered = text.lower()
    asks_disease = any(k in lowered for k in _DISEASE_KEYWORDS)
    has_diagnosed_scan = any(s.get("status") == "diagnosed" for s in context["recent_disease_scans"])
    missing_prompt: Optional[str] = None

    sarvam = SarvamAiAdapter()
    audio_base64: Optional[str] = None
    audio_mime: Optional[str] = None

    if asks_disease and not has_diagnosed_scan:
        missing_prompt = _MISSING_PHOTO_PROMPTS.get(language_code, _MISSING_PHOTO_PROMPTS["en-IN"])
        reply_text = missing_prompt
        sarvam_status = "configured" if sarvam.is_configured else "not_configured"
        if sarvam.is_configured:
            tts = await sarvam.synthesize_speech(reply_text, language_code)
            audio_base64 = tts.get("audio_base64")
            audio_mime = tts.get("audio_mime")
    elif not sarvam.is_configured:
        sarvam_status = "not_configured"
        reply_text = _NOT_CONFIGURED_REPLIES.get(language_code, _NOT_CONFIGURED_REPLIES["en-IN"])
    else:
        sarvam_status = "configured"
        prior_rows = (
            db.query(VoiceMessage)
            .filter(
                VoiceMessage.session_id == session.id,
                VoiceMessage.farmer_id == farmer.id,
                VoiceMessage.id < farmer_msg.id,
            )
            .order_by(VoiceMessage.id.desc())
            .limit(8)
            .all()
        )
        history = [
            {"role": "user" if r.role == "farmer" else "assistant", "content": r.content}
            for r in reversed(prior_rows)
        ]
        system_prompt = _build_system_prompt(language_code, context)
        chat_res = await sarvam.generate_chat_reply(
            system_prompt=system_prompt,
            history=history,
            user_message=text.strip(),
        )
        if chat_res["status"] == "configured" and chat_res["reply"]:
            reply_text = chat_res["reply"]
            tts = await sarvam.synthesize_speech(reply_text, language_code)
            audio_base64 = tts.get("audio_base64")
            audio_mime = tts.get("audio_mime")
        else:
            sarvam_status = "error"
            reply_text = (
                f"Sarvam AI could not complete the reply ({chat_res.get('note', 'upstream error')}). "
                "Please verify SARVAM_API_KEY credits and connectivity."
            )

    assistant_msg = VoiceMessage(
        session_id=session.id,
        farmer_id=farmer.id,
        role="assistant",
        language_code=language_code,
        content=reply_text,
        context_snapshot=context,
    )
    db.add(assistant_msg)
    db.commit()

    all_msgs = (
        db.query(VoiceMessage)
        .filter(VoiceMessage.session_id == session.id, VoiceMessage.farmer_id == farmer.id)
        .order_by(VoiceMessage.id.asc())
        .all()
    )

    return VoiceTurnOut(
        session_id=session.id,
        language_code=language_code,
        recognized_text=text.strip(),
        reply_text=reply_text,
        audio_base64=audio_base64,
        audio_mime=audio_mime,
        sarvam_status=sarvam_status,
        context_used=context,
        missing_data_prompt=missing_prompt,
        messages=all_msgs,
    )


def list_voice_sessions(db: Session, farmer_id: int) -> List[VoiceSession]:
    return (
        db.query(VoiceSession)
        .filter(VoiceSession.farmer_id == farmer_id)
        .order_by(VoiceSession.updated_at.desc())
        .all()
    )


def list_session_messages(db: Session, farmer_id: int, session_id: int) -> List[VoiceMessage]:
    session = (
        db.query(VoiceSession)
        .filter(VoiceSession.id == session_id, VoiceSession.farmer_id == farmer_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice session not found.")
    return (
        db.query(VoiceMessage)
        .filter(VoiceMessage.session_id == session_id, VoiceMessage.farmer_id == farmer.id)
        .order_by(VoiceMessage.id.asc())
        .all()
    )
