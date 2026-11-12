# Environment Variables Guide

Copy `backend/.env.example` to `backend/.env` before running the backend. Never commit `.env` files or put API secrets inside `frontend/`.

| Variable | Service | Registration / Approval Required |
|---|---|---|
| `SECRET_KEY` | JWT signing | Generate a random 32+ byte secret string |
| `DATABASE_URL` | SQLite / PostgreSQL | Local SQLite default; PostgreSQL URL in production |
| `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | LiveKit WebRTC Voice | Free/paid account on LiveKit Cloud or self-hosted LiveKit |
| `SARVAM_API_KEY` | Sarvam AI Saaras/Bulbul/LLM | Developer registration + API credits at sarvam.ai |
| `IMD_API_KEY`, `IMD_USERNAME`, `IMD_PASSWORD` | India Meteorological Dept | Institutional/developer registration + static server IP whitelisting at `api.imd.gov.in` |
| `OPENWEATHER_API_KEY` | OpenWeatherMap (Forecast Fallback) | Free signup (`2.5` free tier) or paid/card-verified (`3.0` One Call) |
| `CWC_API_URL`, `CWC_API_KEY` | Central Water Commission | No public REST API; requires official CWC/NWIC institutional feed |
| `PLANTIX_BASE_URL`, `PLANTIX_API_KEY` | Plantix Intelligence | Commercial B2B partner approval via `b2b.plantix.net` |
| `VISION_MODEL_BASE_URL`, `VISION_MODEL_API_KEY`, `VISION_MODEL_NAME` | Fallback Disease Vision Model | OpenAI/Gemini-compatible multimodal API key |
| `GOOGLE_AGRI_API_KEY` | Google Agricultural Understanding (`ALU`/`AMED`) | Google Cloud project & API access enablement |
| `USDA_FDC_API_KEY` | USDA FoodData Central | Free key via `fdc.nal.usda.gov/api-key-signup/` |
| `NCBI_API_KEY` | NCBI PubMed E-utilities | Optional (3 req/s without key; 10 req/s with free NCBI key) |
| `DATA_GOV_IN_API_KEY` | data.gov.in AGMARKNET & Schemes | Free registration at `data.gov.in` |
| `CEDA_API_KEY` | CEDA Ashoka Agmarknet | Free non-commercial signup at `ceda.ashoka.edu.in` |
| `ENAM_API_URL` | e-NAM | No public self-service REST API; partner feed only |
| `APISETU_API_KEY`, `APISETU_CLIENT_ID` | API Setu myScheme | Developer registration at `directory.apisetu.gov.in` |
| `FERTILIZER_PRICE_API_URL`, `FERTILIZER_PRICE_API_KEY` | Verified Fertilizer MRP Feed | Official/partner dated price feed |
