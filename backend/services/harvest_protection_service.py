"""Crop-specific harvest protection & farmer profit optimization decision engine."""

from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models.crop import TrackedCrop
from models.farmer import Farmer
from schemas.harvest import (
    HarvestAnalyzeRequest,
    HarvestProfitOptimizationOut,
    HarvestProtectionItemOut,
    HarvestProtectionSummaryOut,
)
from schemas.weather import WeatherFloodOut
from services.crop_service import list_tracked_crops
from services.mandi_service import get_mandi_prices_report
from services.weather_service import get_weather_and_flood_summary


_HARVEST_PROFILES: Dict[str, Dict] = {
    "tomato": {
        "maturity_days": (75, 110),
        "rain_vulnerability": "high_spoilage",
        "maturity_markers": "Breaker-to-pink stage for distant mandi transport; firm red for local fresh sale.",
        "ready_rain_en": (
            "Your tomato crop is {readiness}. Heavy rainfall (~{rain:.1f} mm) is expected within 24-48 hours. "
            "Inspect fruits for breaker/pink maturity and harvest market-ready fruits before the rain to prevent fruit cracking and late blight."
        ),
        "ready_rain_kn": (
            "ನಿಮ್ಮ ಟೊಮೇಟೊ ಬೆಳೆ {readiness_kn}. ಮುಂದಿನ 24-48 ಗಂಟೆಗಳಲ್ಲಿ ಭಾರೀ ಮಳೆ (~{rain:.1f} ಮಿ.ಮೀ) ಸಾಧ್ಯತೆಯಿದೆ. "
            "ಬೆಳೆ ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದ್ದರೆ, ಮಳೆಯ ಮುನ್ನವೇ ಮಾರುಕಟ್ಟೆ ಯೋಗ್ಯ ಹಣ್ಣುಗಳನ್ನು ಕೊಯ್ಲು ಮಾಡಿ ಬಿರುಕು ಮತ್ತು ಕೊಳೆ ರೋಗ ತಡೆಯಿರಿ."
        ),
        "immature_rain_en": (
            "Your tomato crop is still immature ({days_rem} days left before harvest readiness). Do NOT harvest unripe fruits despite rain forecast. "
            "Instead, clear inter-row drainage channels, tighten bamboo/wire staking against wind, and inspect foliage for early/late blight post-rain."
        ),
        "immature_rain_kn": (
            "ನಿಮ್ಮ ಟೊಮೇಟೊ ಬೆಳೆ ಇನ್ನೂ ಪಕ್ವವಾಗಿಲ್ಲ (ಕೊಯ್ಲಿಗೆ {days_rem} ದಿನ ಬಾಕಿ ಇದೆ). ಮಳೆ ಮುನ್ಸೂಚನೆ ಇರುವುದರಿಂದ ಅಪಕ್ವ ಕಾಯಿಗಳನ್ನು ಕೊಯ್ಯಬೇಡಿ. "
            "ಬದಲಿಗೆ ಸಾಲುಗಳ ನಡುವಿನ ನೀರು ಬಸಿದುಹೋಗುವಂತೆ ಕಾಲುವೆ ಸ್ವಚ್ಛಗೊಳಿಸಿ ಮತ್ತು ಕಂಬ/ತಂತಿ ಆಧಾರವನ್ನು ಭದ್ರಪಡಿಸಿ."
        ),
        "dry_ready_en": (
            "Tomato crop has reached harvest maturity with dry conditions ahead. Pick early morning into ventilated plastic crates, grade by size/color, and avoid stacking high."
        ),
        "dry_ready_kn": (
            "ಟೊಮೇಟೊ ಬೆಳೆ ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದ್ದು ಒಣ ಹವಾಮಾನವಿದೆ. ಬೆಳಗಿನ ತಂಪಾದ ಸಮಯದಲ್ಲಿ ಕೊಯ್ಲು ಮಾಡಿ ಗಾಳಿಯಾಡುವ ಕ್ರೇಟ್‌ಗಳಲ್ಲಿ ವರ್ಗೀಕರಿಸಿ ಸಾಗಿಸಿ."
        ),
        "precautions_en": [
            "Pick market-ready breaker/pink fruits before rain onset; leave green immature fruits on plant.",
            "Keep harvested crates off wet ground under a ventilated shed.",
            "Clear furrow drainage immediately so roots do not sit in standing water.",
        ],
        "precautions_kn": [
            "ಮಳೆ ಬರುವ ಮೊದಲು ಮಾಗಿದ/ಗುಲಾಬಿ ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿದ ಟೊಮೇಟೊಗಳನ್ನು ಮಾತ್ರ ಕೊಯ್ಯಿರಿ; ಹಸಿ ಕಾಯಿಗಳನ್ನು ಬಿಡಿ.",
            "ಕೊಯ್ದ ಕ್ರೇಟ್‌ಗಳನ್ನು ಒದ್ದೆ ನೆಲದ ಮೇಲೆ ಇಡದೆ ನೆರಳಿನ ಗಾಳಿಯಾಡುವ ಸ್ಥಳದಲ್ಲಿ ಇಡಿ.",
            "ಬೇರುಗಳ ಬಳಿ ನೀರು ನಿಲ್ಲದಂತೆ ತಕ್ಷಣ ಕಾಲುವೆಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
        ],
    },
    "paddy": {
        "maturity_days": (120, 140),
        "rain_vulnerability": "grain_sprouting_lodging",
        "maturity_markers": "80-85% straw-colored panicles with ~20-22% grain moisture.",
        "ready_rain_en": (
            "Your paddy crop has {readiness} and rain (~{rain:.1f} mm) is forecast. If 80%+ panicles are golden-straw, harvest promptly before lodging/germination on panicles; "
            "keep tarpaulins ready for immediate threshing-floor cover."
        ),
        "ready_rain_kn": (
            "ನಿಮ್ಮ ಭತ್ತದ ಬೆಳೆ {readiness_kn} ಮತ್ತು ಮಳೆ (~{rain:.1f} ಮಿ.ಮೀ) ಮುನ್ಸೂಚನೆಯಿದೆ. 80%+ ತೆನೆಗಳು ಬಂಗಾರದ ಬಣ್ಣಕ್ಕೆ ತಿರುಗಿದ್ದರೆ ಬೆಳೆ ಬೀಳುವ ಹಾಗೂ ಮೊಳಕೆಯೊಡೆಯುವ ಮುನ್ನ ಕೊಯ್ಲು ಮಾಡಿ ಟಾರ್ಪಾಲಿನ್ ಸಿದ್ಧವಿಡಿ."
        ),
        "immature_rain_en": (
            "Your paddy crop is still in the immature grain-filling/vegetative phase ({days_rem} days to maturity). Do NOT harvest early. "
            "Lower excess bund water if fields are already flooded and monitor for neck blast / brown plant hopper in humid weather."
        ),
        "immature_rain_kn": (
            "ನಿಮ್ಮ ಭತ್ತದ ಬೆಳೆ ಇನ್ನೂ ಅಪಕ್ವ ಹಂತದಲ್ಲಿದೆ (ಕೊಯ್ಲಿಗೆ {days_rem} ದಿನ ಬಾಕಿ). ಅವಧಿಗೂ ಮುನ್ನ ಕೊಯ್ಲು ಮಾಡಬೇಡಿ. "
            "ಗದ್ದೆಯಲ್ಲಿ ಹೆಚ್ಚುವರಿ ನೀರಿದ್ದರೆ ಬಸಿದು ಬಿಡಿ ಹಾಗೂ ತೇವಾಂಶದಲ್ಲಿ ಕೀಟ/ಬೆಂಕಿ ರೋಗ ಗಮನಿಸಿ."
        ),
        "dry_ready_en": (
            "Paddy panicles have reached harvest maturity under favorable dry weather. Harvest at ~20% grain moisture and sun-dry down to 13-14% before storage."
        ),
        "dry_ready_kn": (
            "ಭತ್ತದ ಬೆಳೆ ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದ್ದು ಒಣ ಹವಾಮಾನ ಅನುಕೂಲಕರವಾಗಿದೆ. ಕೊಯ್ಲು ಮಾಡಿ ಸಂಗ್ರಹಿಸುವ ಮೊದಲು ಕಾಳಿನ ತೇವಾಂಶವನ್ನು 13-14% ಗೆ ಒಣಗಿಸಿ."
        ),
        "precautions_en": [
            "Drain standing field water 7-10 days before harvest so harvesters do not bog down.",
            "Do not heap wet harvested bundles in the field—cover immediately with waterproof tarpaulins.",
            "Dry threshed paddy to <=14% moisture before bagging to prevent aflatoxin/discoloration.",
        ],
        "precautions_kn": [
            "ಕೊಯ್ಲಿಗೆ 7-10 ದಿನ ಮೊದಲು ಗದ್ದೆಯ ನೀರನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ಹರಿಸಿ.",
            "ಕೊಯ್ದ ಒದ್ದೆ ಭತ್ತದ ಕಟ್ಟುಗಳನ್ನು ಹೊಲದಲ್ಲಿ ರಾಶಿ ಹಾಕಬೇಡಿ; ತಕ್ಷಣ ಟಾರ್ಪಾಲಿನ್ ಹೊದಿಸಿ.",
            "ಚೀಲಗಳಿಗೆ ತುಂಬುವ ಮೊದಲು ಧಾನ್ಯವನ್ನು 14% ತೇವಾಂಶಕ್ಕಿಂತ ಕಡಿಮೆ ಮಟ್ಟಕ್ಕೆ ಒಣಗಿಸಿ.",
        ],
    },
    "chilli": {
        "maturity_days": (85, 135),
        "rain_vulnerability": "anthracnose_dieback",
        "maturity_markers": "Firm glossy green pods for fresh picking, or uniform deep-red pods for dry chilli.",
        "ready_rain_en": (
            "Your chilli crop has mature pickable pods ahead of forecast rain (~{rain:.1f} mm). Pick mature pods immediately to reduce anthracnose fruit-rot and pod bleaching, and shift pods under dry ventilated cover."
        ),
        "ready_rain_kn": (
            "ನಿಮ್ಮ ಮೆಣಸಿನಕಾಯಿ ಬೆಳೆಯಲ್ಲಿ ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾದ ಕಾಯಿಗಳಿದ್ದು ಮಳೆ (~{rain:.1f} ಮಿ.ಮೀ) ಮುನ್ಸೂಚನೆಯಿದೆ. ಹಣ್ಣು ಕೊಳೆ ರೋಗ ತಪ್ಪಿಸಲು ಸಿದ್ಧ ಕಾಯಿಗಳನ್ನು ತಕ್ಷಣ ಕಿತ್ತು ಒಣ ಜಾಗದಲ್ಲಿ ಇಡಿ."
        ),
        "immature_rain_en": (
            "Your chilli crop is still developing ({days_rem} days remaining). Do NOT harvest immature pods. Ensure raised-bed drainage to prevent Phytophthora root rot."
        ),
        "immature_rain_kn": (
            "ನಿಮ್ಮ ಮೆಣಸಿನಕಾಯಿ ಬೆಳೆ ಇನ್ನೂ ಬೆಳೆಯುವ ಹಂತದಲ್ಲಿದೆ (ಕೊಯ್ಲಿಗೆ {days_rem} ದಿನ ಬಾಕಿ). ಅಪಕ್ವ ಕಾಯಿಗಳನ್ನು ಕೀಳಬೇಡಿ; ಬೇರು ಕೊಳೆಯದಂತೆ ಬಸಿಗಾಲುವೆ ಸರಿಪಡಿಸಿ."
        ),
        "dry_ready_en": (
            "Dry weather favors uniform chilli picking and sun-drying on clean raised tarpaulins/nets to preserve capsaicin color."
        ),
        "dry_ready_kn": (
            "ಒಣ ಹವಾಮಾನ ಮೆಣಸಿನಕಾಯಿ ಕೊಯ್ಲು ಮತ್ತು ಶುದ್ಧ ಟಾರ್ಪಾಲಿನ್ ಮೇಲೆ ಒಣಗಿಸಲು ಅತ್ಯುತ್ತಮವಾಗಿದೆ."
        ),
        "precautions_en": [
            "Never dry damp chillies directly on soil; use clean raised shade/tarpaulins with turning.",
            "Pick glossy mature pods before rain; remove any anthracnose-spotted pods separately.",
        ],
        "precautions_kn": [
            "ಒದ್ದೆ ಮೆಣಸಿನಕಾಯಿಯನ್ನು ನೇರವಾಗಿ ನೆಲದ ಮೇಲೆ ಒಣಗಿಸಬೇಡಿ; ಶುದ್ಧ ಟಾರ್ಪಾಲಿನ್ ಬಳಸಿ.",
            "ಕೊಳೆತ ಕಾಯಿಗಳನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ ಸುರಕ್ಷಿತವಾಗಿ ವಿಲೇವಾರಿ ಮಾಡಿ.",
        ],
    },
    "maize": {
        "maturity_days": (95, 115),
        "rain_vulnerability": "cob_rot_lodging",
        "maturity_markers": "Dry brown husks and black layer formation at kernel base.",
        "ready_rain_en": (
            "Your maize cobs have black-layer maturity ahead of rain/wind (~{rain:.1f} mm). Harvest mature cobs before strong winds lodge stalks and cause ear rot, and shelter cobs before shelling."
        ),
        "ready_rain_kn": (
            "ನಿಮ್ಮ ಮೆಕ್ಕೆಜೋಳದ ತೆನೆಗಳು ಕೊಯ್ಲಿಗೆ ಪಕ್ವವಾಗಿವೆ ಮತ್ತು ಮಳೆ/ಗಾಳಿ (~{rain:.1f} ಮಿ.ಮೀ) ಮುನ್ಸೂಚನೆಯಿದೆ. ತೆನೆ ಕೊಳೆಯುವ ಮತ್ತು ಗಿಡ ಬೀಳುವ ಮುನ್ನ ಕೊಯ್ಲು ಮಾಡಿ ಸುರಕ್ಷಿತವಾಗಿ ಸಂಗ್ರಹಿಸಿ."
        ),
        "immature_rain_en": (
            "Your maize crop is still filling kernels ({days_rem} days left). Do NOT harvest milky/dough-stage cobs. Maintain ridge-and-furrow drainage against waterlogging."
        ),
        "immature_rain_kn": (
            "ನಿಮ್ಮ ಮೆಕ್ಕೆಜೋಳ ಇನ್ನೂ ಹಾಲು/ಕಾಳು ತುಂಬುವ ಹಂತದಲ್ಲಿದೆ (ಕೊಯ್ಲಿಗೆ {days_rem} ದಿನ ಬಾಕಿ). ಅಪಕ್ವ ತೆನೆಗಳನ್ನು ಕೊಯ್ಯಬೇಡಿ; ನೀರು ನಿಲ್ಲದಂತೆ ಬಸಿಗಾಲುವೆ ಗಮನಿಸಿ."
        ),
        "dry_ready_en": (
            "Maize has reached physiological maturity under dry conditions. Harvest cobs and dry grain to <13% moisture for best mandi grade."
        ),
        "dry_ready_kn": (
            "ಮೆಕ್ಕೆಜೋಳ ಕೊಯ್ಲಿಗೆ ಪಕ್ವವಾಗಿದೆ. ಒಣ ಹವಾಮಾನದಲ್ಲಿ ಕೊಯ್ಲು ಮಾಡಿ ಕಾಳಿನ ತೇವಾಂಶ 13% ಕ್ಕಿಂತ ಕಡಿಮೆ ಇರುವಂತೆ ಒಣಗಿಸಿ."
        ),
        "precautions_en": [
            "Check kernel black layer before harvesting; avoid shelling wet cobs.",
            "Store dehusked cobs off the floor with airflow if immediate shelling is delayed by humidity.",
        ],
        "precautions_kn": [
            "ಕಾಳಿನ ಬುಡದಲ್ಲಿ ಕಪ್ಪು ಚುಕ್ಕೆ (black layer) ದೃಢಪಡಿಸಿದ ನಂತರವೇ ಕೊಯ್ಲು ಮಾಡಿ.",
            "ತೇವಾಂಶ ಹೆಚ್ಚಿದ್ದರೆ ಒಣಗಿದ ನಂತರವೇ ಕಾಳು ಬೇರ್ಪಡಿಸಿ.",
        ],
    },
    "ragi": {
        "maturity_days": (105, 120),
        "rain_vulnerability": "earhead_sprouting",
        "maturity_markers": "Brown earheads and hard grain that detaches cleanly on rubbing.",
        "ready_rain_en": (
            "Your ragi earheads are ready for harvest ahead of rain (~{rain:.1f} mm). Cut mature earheads promptly to prevent in-earhead grain sprouting and mold."
        ),
        "ready_rain_kn": (
            "ನಿಮ್ಮ ರಾಗಿ ತೆನೆಗಳು ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದ್ದು ಮಳೆ (~{rain:.1f} ಮಿ.ಮೀ) ಮುನ್ಸೂಚನೆಯಿದೆ. ತೆನೆಯಲ್ಲೇ ಕಾಳು ಮೊಳಕೆಯೊಡೆಯದಂತೆ ಮಳೆಯ ಮುನ್ನವೇ ಕಟಾವು ಮಾಡಿ."
        ),
        "immature_rain_en": (
            "Your ragi crop is not mature yet ({days_rem} days left). Do NOT cut unripe green earheads. Open field drainage outlets if heavy rain arrives."
        ),
        "immature_rain_kn": (
            "ನಿಮ್ಮ ರಾಗಿ ಬೆಳೆ ಇನ್ನೂ ಹಸಿರಾಗಿದ್ದು ಪಕ್ವವಾಗಿಲ್ಲ (ಕೊಯ್ಲಿಗೆ {days_rem} ದಿನ ಬಾಕಿ). ಅಪಕ್ವ ತೆನೆಗಳನ್ನು ಕತ್ತರಿಸಬೇಡಿ; ನೀರು ನಿಲ್ಲದಂತೆ ಬದುಗಳನ್ನು ತೆರೆಯಿರಿ."
        ),
        "dry_ready_en": (
            "Ragi has reached dry harvest maturity. Cut earheads in dry morning hours and cure under bright sun before threshing."
        ),
        "dry_ready_kn": (
            "ರಾಗಿ ಕಟಾವಿಗೆ ಸಿದ್ಧವಾಗಿದೆ. ಬಿಸಿಲಿನ ಸಮಯದಲ್ಲಿ ಕಟಾವು ಮಾಡಿ ಚೆನ್ನಾಗಿ ಒಣಗಿಸಿ ಬಡಿದುಕೊಳ್ಳಿ."
        ),
        "precautions_en": [
            "Dry cut earheads under cover if sudden showers occur.",
            "Avoid stacking damp stalks tightly to prevent heating and fungal spoilage.",
        ],
        "precautions_kn": [
            "ದಿನದ ಮಧ್ಯದಲ್ಲಿ ಮಳೆ ಬಂದರೆ ಕಟಾವು ಮಾಡಿದ ತೆನೆಗಳನ್ನು ಟಾರ್ಪಾಲಿನ್ ಕೆಳಗೆ ಇಡಿ.",
        ],
    },
}

_DEFAULT_PROFILE: Dict = {
    "maturity_days": (100, 125),
    "rain_vulnerability": "general_moisture",
    "maturity_markers": "Crop-specific physiological maturity markers (dry pods/husks or market-firm fruit color).",
    "ready_rain_en": (
        "Your {crop} crop is {readiness} and rain (~{rain:.1f} mm) is expected within 24-48 hours. "
        "Inspect maturity and harvest market-ready produce before rain if dry storage is available."
    ),
    "ready_rain_kn": (
        "ನಿಮ್ಮ {crop} ಬೆಳೆ {readiness_kn} ಮತ್ತು ಮುಂದಿನ 24-48 ಗಂಟೆಗಳಲ್ಲಿ ಮಳೆ (~{rain:.1f} ಮಿ.ಮೀ) ಸಾಧ್ಯತೆಯಿದೆ. "
        "ಪಕ್ವತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ, ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾದ ಬೆಳೆಯನ್ನು ಮಳೆಯ ಮುನ್ನ ಸುರಕ್ಷಿತವಾಗಿ ಕೊಯ್ಲು ಮಾಡಿ."
    ),
    "immature_rain_en": (
        "Your {crop} crop is still immature ({days_rem} days before harvest window). Do NOT harvest prematurely due to rain. "
        "Focus on clearing field drainage and protecting young plants."
    ),
    "immature_rain_kn": (
        "ನಿಮ್ಮ {crop} ಬೆಳೆ ಇನ್ನೂ ಪಕ್ವವಾಗಿಲ್ಲ (ಕೊಯ್ಲಿಗೆ {days_rem} ದಿನ ಬಾಕಿ). ಮಳೆ ಕಾರಣದಿಂದ ಅವಧಿಗೂ ಮುನ್ನ ಕೊಯ್ಲು ಮಾಡಬೇಡಿ. "
        "ಹೊಲದ ಬಸಿಗಾಲುವೆ ಸ್ವಚ್ಛಗೊಳಿಸಿ ಬೆಳೆಯನ್ನು ರಕ್ಷಿಸಿ."
    ),
    "dry_ready_en": "{crop} has reached harvest readiness under dry weather. Proceed with clean harvesting and grading.",
    "dry_ready_kn": "{crop} ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದ್ದು ಒಣ ಹವಾಮಾನವಿದೆ. ಶುದ್ಧವಾಗಿ ಕೊಯ್ಲು ಮತ್ತು ವರ್ಗೀಕರಣ ಮಾಡಿ.",
    "precautions_en": [
        "Verify field drainage before forecast showers.",
        "Keep harvested produce under dry, ventilated shelter away from moisture.",
    ],
    "precautions_kn": [
        "ಮಳೆಯ ಮುನ್ನ ಹೊಲದ ನೀರು ಬಸಿದುಹೋಗುವ ಕಾಲುವೆಗಳನ್ನು ಪರೀಕ್ಷಿಸಿ.",
        "ಕೊಯ್ದ ಬೆಳೆಯನ್ನು ಒಣ, ಗಾಳಿಯಾಡುವ ಸ್ಥಳದಲ್ಲಿ ಸುರಕ್ಷಿತವಾಗಿ ಸಂಗ್ರಹಿಸಿ.",
    ],
}


def _match_profile(crop_name: str) -> Dict:
    key = crop_name.strip().lower()
    for token, prof in _HARVEST_PROFILES.items():
        if token in key or (token == "paddy" and "rice" in key):
            return prof
    return _DEFAULT_PROFILE


async def evaluate_crop_harvest_protection(
    *,
    farmer: Farmer,
    crop_id: Optional[int],
    crop_name: str,
    variety: Optional[str],
    sowing_date: date,
    current_stage: str,
    weather: WeatherFloodOut,
) -> HarvestProtectionItemOut:
    profile = _match_profile(crop_name)
    min_days, max_days = profile["maturity_days"]
    today = date.today()
    age_days = max(0, (today - sowing_date).days)
    expected_maturity = sowing_date + timedelta(days=min_days)
    days_remaining = max(0, (expected_maturity - today).days)

    stage_norm = (current_stage or "vegetative").strip().lower()
    if stage_norm in {"germination", "vegetative", "flowering"} and days_remaining > 10:
        readiness = "immature"
    elif days_remaining == 0 and age_days > max_days + 7:
        readiness = "overdue"
    elif stage_norm == "maturity" or days_remaining == 0:
        readiness = "harvest_ready"
    elif days_remaining <= 10 or stage_norm == "fruiting":
        readiness = "approaching_maturity"
    else:
        readiness = "immature"

    hourly = weather.forecast
    daily = weather.daily_forecast
    rain_24h = round(sum(p.rain_mm for p in hourly[:24]), 1)
    rain_72h = round(sum(d.rain_sum_mm for d in daily[:3]), 1) if daily else round(sum(p.rain_mm for p in hourly[:48]), 1)
    if daily and len(daily) > 1:
        rain_24h = max(rain_24h, daily[0].rain_sum_mm, daily[1].rain_sum_mm)
    max_prob = max(
        [p.rain_probability_pct for p in hourly[:48]] + [d.rain_probability_pct for d in daily[:3]] + [0.0]
    )
    max_wind = max(
        [max(p.wind_kmh, p.wind_gust_kmh) for p in hourly[:48]] + [d.wind_max_kmh for d in daily[:3]] + [0.0]
    )

    heavy_rain_soon = rain_24h >= 20.0 or max_prob >= 70.0 or any(
        a.alert_type in {"heavy_rainfall_warning", "official_flood_warning"} for a in weather.classified_alerts
    )
    moderate_rain_soon = rain_72h >= 12.0 or max_prob >= 50.0

    # Decision engine respecting HARD MATURITY GUARD
    if readiness == "immature":
        if heavy_rain_soon or max_wind >= 40.0 or moderate_rain_soon:
            action = "protect_crop"
            action_en = "Do Not Harvest — Protect Growing Crop"
            action_kn = "ಕೊಯ್ಲು ಬೇಡ — ಬೆಳೆ ರಕ್ಷಣಾ ಕ್ರಮ ತೆಗೆದುಕೊಳ್ಳಿ"
            explanation_en = profile["immature_rain_en"].format(crop=crop_name, days_rem=days_remaining)
            explanation_kn = profile["immature_rain_kn"].format(crop=crop_name, days_rem=days_remaining)
        else:
            action = "wait_for_maturity"
            action_en = "Wait for Physiological Maturity"
            action_kn = "ಬೆಳೆ ಪಕ್ವವಾಗುವವರೆಗೆ ಕಾಯಿರಿ"
            explanation_en = (
                f"{crop_name} is {age_days} days old (about {days_remaining} days left before harvest window). "
                f"Maintain normal irrigation and check maturity marker: {profile['maturity_markers']}"
            )
            explanation_kn = (
                f"{crop_name} ಬೆಳೆಗೆ ಈಗ {age_days} ದಿನಗಳಾಗಿದ್ದು ಕೊಯ್ಲಿಗೆ ಇನ್ನೂ ಸುಮಾರು {days_remaining} ದಿನ ಬಾಕಿ ಇದೆ. "
                "ನಿಯಮಿತ ನೀರಾವರಿ ಹಾಗೂ ಪೋಷಕಾಂಶ ನಿರ್ವಹಣೆ ಮುಂದುವರಿಸಿ."
            )
    elif readiness in {"harvest_ready", "overdue"}:
        if heavy_rain_soon:
            action = "harvest_now"
            action_en = "Harvest Market-Ready Produce Immediately Before Rain"
            action_kn = "ಮಳೆಯ ಮುನ್ನವೇ ತಕ್ಷಣ ಕೊಯ್ಲು ಮಾಡಿ"
            explanation_en = profile["ready_rain_en"].format(
                crop=crop_name, readiness="ready for harvesting", rain=max(rain_24h, rain_72h)
            )
            explanation_kn = profile["ready_rain_kn"].format(
                crop=crop_name, readiness_kn="ಕೊಯ್ಲಿಗೆ ಸಿದ್ಧವಾಗಿದೆ", rain=max(rain_24h, rain_72h)
            )
        elif moderate_rain_soon and profile["rain_vulnerability"] == "general_moisture":
            action = "delay_harvest"
            action_en = "Monitor Short Dry Window Before Cutting"
            action_kn = "ಒಣ ಸಮಯ ನೋಡಿ ಕೊಯ್ಲು ಯೋಜಿಸಿ"
            explanation_en = (
                f"Passing showers ({max_prob:.0f}% probability) may wet harvested produce. Pick only what can be dried/covered today, or wait for the next dry 24h spell."
            )
            explanation_kn = (
                f"ಸಾಧಾರಣ ಮಳೆ ({max_prob:.0f}% ಸಾಧ್ಯತೆ) ನಿರೀಕ್ಷೆಯಿರುವುದರಿಂದ, ಇಂದು ಒಣಗಿಸಬಹುದಾದಷ್ಟೇ ಕೊಯ್ಲು ಮಾಡಿ ಅಥವಾ ಮುಂದಿನ ಒಣ ದಿನಕ್ಕೆ ಕಾಯಿರಿ."
            )
        else:
            action = "harvest_now"
            action_en = "Optimal Dry Harvest Window"
            action_kn = "ಕೊಯ್ಲಿಗೆ ಅತ್ಯುತ್ತಮ ಒಣ ಹವಾಮಾನ"
            explanation_en = profile["dry_ready_en"].format(crop=crop_name)
            explanation_kn = profile["dry_ready_kn"].format(crop=crop_name)
    else:  # approaching_maturity
        if heavy_rain_soon:
            action = "prepare_harvest"
            action_en = "Inspect Maturity & Harvest Ready Portion Before Rain"
            action_kn = "ಪಕ್ವತೆ ಪರಿಶೀಲಿಸಿ ಸಿದ್ಧ ಬೆಳೆಯನ್ನು ಮಳೆಯ ಮುನ್ನ ಕೊಯ்யಿರಿ"
            explanation_en = profile["ready_rain_en"].format(
                crop=crop_name, readiness="approaching maturity", rain=max(rain_24h, rain_72h)
            )
            explanation_kn = profile["ready_rain_kn"].format(
                crop=crop_name, readiness_kn="ಕೊಯ್ಲಿನ ಹಂತಕ್ಕೆ ತಲುಪುತ್ತಿದೆ", rain=max(rain_24h, rain_72h)
            )
        else:
            action = "prepare_harvest"
            action_en = "Prepare Crates, Tarpaulins & Grading Area"
            action_kn = "ಕೊಯ್ಲು ಸಿದ್ಧತೆ (ಕ್ರೇಟ್/ಟಾರ್ಪಾಲಿನ್) ಮಾಡಿಕೊಳ್ಳಿ"
            explanation_en = (
                f"{crop_name} is approaching maturity (~{days_remaining} days). Watch for: {profile['maturity_markers']}"
            )
            explanation_kn = (
                f"{crop_name} ಬೆಳೆ ಕೊಯ್ಲಿನ ಹಂತದಲ್ಲಿದೆ (~{days_remaining} ದಿನ ಬಾಕಿ). ಪಕ್ವತೆಯ ಲಕ್ಷಣಗಳನ್ನು ಪ್ರತಿದಿನ ಗಮನಿಸಿ."
            )

    # Profit & Post-Harvest Optimization combining live mandi lookup (when configured)
    mandi = await get_mandi_prices_report(
        commodity=crop_name,
        state=farmer.state,
        district=farmer.district,
        include_demo=False,
    )
    latest_mandi = mandi.records[0] if mandi.records else None
    spoilage_risk = (
        "high"
        if (heavy_rain_soon and profile["rain_vulnerability"] in {"high_spoilage", "anthracnose_dieback"})
        else "moderate"
        if heavy_rain_soon or moderate_rain_soon
        else "low"
    )
    sell_strategy = (
        "Harvest breaker/grade-A produce immediately, pre-cool/dry under shelter, and dispatch before heavy rain disrupts rural roads."
        if readiness in {"harvest_ready", "approaching_maturity", "overdue"} and heavy_rain_soon
        else "Grade produce by size/maturity and stagger dispatch to avoid distress glut selling."
        if readiness in {"harvest_ready", "overdue"}
        else "Hold harvest until full physiological maturity so weight and Brix/grade quality attract better APMC bids."
    )
    transport_advice = (
        "Dispatch in covered/tarpaulin-protected transport early morning before forecast showers."
        if heavy_rain_soon or moderate_rain_soon
        else "Schedule morning dispatch when temperatures are cool to minimize weight loss."
    )
    if latest_mandi:
        opt_en = (
            f"Latest available {latest_mandi.market} mandi modal rate is Rs {latest_mandi.modal_price:.0f}/qtl ({latest_mandi.arrival_date}). "
            f"{sell_strategy}"
        )
        opt_kn = (
            f"{latest_mandi.market} ಮಂಡಿಯಲ್ಲಿ ಇತ್ತೀಚಿನ ಮಾದರಿ ದರ ಕ್ವಿಂಟಾಲ್‌ಗೆ ₹{latest_mandi.modal_price:.0f} ({latest_mandi.arrival_date}). "
            "ಗುಣಮಟ್ಟ ವರ್ಗೀಕರಣ ಮಾಡಿ ತೇವಾಂಶದಿಂದ ರಕ್ಷಿಸಿ ಮಾರಾಟ ಮಾಡುವುದರಿಂದ ನಷ್ಟ ತಪ್ಪಿಸಬಹುದು."
        )
    else:
        opt_en = (
            "Live mandi feed key (DATA_GOV_IN_API_KEY / CEDA_API_KEY) is not configured, so no live APMC price is invented. "
            f"{sell_strategy}"
        )
        opt_kn = (
            "ಲೈವ್ ಮಂಡಿ ದರ API ಕಾನ್ಫಿಗರ್ ಆಗದಿರುವುದರಿಂದ ಅಂದಾಜು ದರ ತೋರಿಸಲಾಗುವುದಿಲ್ಲ. "
            "ಗುಣಮಟ್ಟ ಮತ್ತು ತೇವಾಂಶ ನಿಯಂತ್ರಣದಿಂದ ಕೊಯ್ಲು ನಂತರದ ನಷ್ಟವನ್ನು ಕಡಿಮೆ ಮಾಡಬಹುದು."
        )

    return HarvestProtectionItemOut(
        crop_id=crop_id,
        crop_name=crop_name,
        variety=variety,
        sowing_date=sowing_date.isoformat(),
        crop_age_days=age_days,
        current_stage=stage_norm,
        expected_maturity_date=expected_maturity.isoformat(),
        days_remaining_to_maturity=days_remaining,
        readiness_status=readiness,
        action=action,
        action_label_en=action_en,
        action_label_kn=action_kn,
        rain_24h_mm=rain_24h,
        rain_72h_mm=rain_72h,
        max_rain_probability_pct=round(max_prob, 0),
        max_wind_kmh=round(max_wind, 1),
        location_label=weather.location_label,
        headline_en=f"{crop_name}: {action_en}",
        headline_kn=f"{crop_name}: {action_kn}",
        explanation_en=explanation_en,
        explanation_kn=explanation_kn,
        crop_specific_notes=[
            f"Crop maturity marker: {profile['maturity_markers']}",
            f"Rain sensitivity profile: {profile['rain_vulnerability'].replace('_', ' ')}",
        ],
        precautions_en=profile["precautions_en"],
        precautions_kn=profile["precautions_kn"],
        profit_optimization=HarvestProfitOptimizationOut(
            market_price_status="configured" if latest_mandi else "not_configured",
            current_modal_price_inr_qtl=latest_mandi.modal_price if latest_mandi else None,
            market_name=latest_mandi.market if latest_mandi else None,
            price_date=latest_mandi.arrival_date if latest_mandi else None,
            spoilage_risk_level=spoilage_risk,
            recommended_sell_strategy=sell_strategy,
            transport_timing_advice=transport_advice,
            explanation_en=opt_en,
            explanation_kn=opt_kn,
            honesty_note="Market optimization guides spoilage reduction & grading; market returns are never guaranteed.",
        ),
    )


async def get_farmer_harvest_protection(
    db: Session,
    farmer: Farmer,
    *,
    weather_override: Optional[WeatherFloodOut] = None,
) -> HarvestProtectionSummaryOut:
    crops: List = list_tracked_crops(db, farmer.id)
    weather = weather_override or await get_weather_and_flood_summary(farmer)
    decisions: List[HarvestProtectionItemOut] = []
    for c in crops:
        if c.status != "active":
            continue
        item = await evaluate_crop_harvest_protection(
            farmer=farmer,
            crop_id=c.id,
            crop_name=c.crop_name,
            variety=c.variety,
            sowing_date=c.sowing_date,
            current_stage=c.current_stage,
            weather=weather,
        )
        decisions.append(item)
    return HarvestProtectionSummaryOut(
        location_label=weather.location_label,
        weather_freshness=weather.freshness_label,
        decisions=decisions,
    )


async def analyze_custom_crop_harvest(
    farmer: Farmer,
    payload: HarvestAnalyzeRequest,
    *,
    weather_override: Optional[WeatherFloodOut] = None,
) -> HarvestProtectionItemOut:
    weather = weather_override or await get_weather_and_flood_summary(farmer)
    return await evaluate_crop_harvest_protection(
        farmer=farmer,
        crop_id=None,
        crop_name=payload.crop_name,
        variety=payload.variety,
        sowing_date=payload.sowing_date,
        current_stage=payload.current_stage,
        weather=weather,
    )
