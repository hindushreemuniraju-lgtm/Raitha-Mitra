# Raitha Mitra — Architecture & Implementation Plan

**Brand:** Raitha Mitra  
**Tagline:** *Your Smart Farming Companion*  
**Workspace Root:** `C:\PROJECTS\raitha-mitra`

---

## 1. System Architecture

Raitha Mitra follows a cleanly decoupled three-tier architecture designed for Indian smallholder farmers (mobile-first web client, asynchronous Python API server, and real-time voice agent worker):

```
+-------------------------------------------------------------------------+
|                       Frontend (React + TypeScript)                     |
|  Vite + Tailwind CSS + Framer Motion + Recharts + Lucide React          |
|  - Mobile-first responsive shell (bottom bar + desktop sidebar)         |
|  - Typed API client (services/api.ts) with JWT bearer interceptor       |
|  - LiveKit WebRTC voice client + browser audio fallback                 |
+------------------------------------+------------------------------------+
                                     | HTTPS / WSS (REST + WebSocket)
+------------------------------------v------------------------------------+
|                      Backend API (Python + FastAPI)                     |
|  routers/  -> HTTP validation, rate limiting, per-farmer JWT auth       |
|  services/ -> Pure agronomic & business logic, DB orchestration         |
|  models/   -> SQLAlchemy ORM (PostgreSQL prod / SQLite local dev)       |
|  schemas/  -> Pydantic v2 request/response contracts                    |
|  utils/    -> Security, JWT, file validation, logging, cache, retries   |
|  integrations/ -> Isolated external API adapters (zero business logic)  |
+------------------------------------+------------------------------------+
                                     |
          +--------------------------+--------------------------+
          |                                                     |
+---------v---------+                                 +---------v---------+
| SQLite / Postgres |                                 | LiveKit Agents    |
| (Alembic managed) |                                 | Voice Worker      |
+-------------------+                                 | Sarvam Saaras STT |
                                                      | Sarvam Bulbul TTS |
                                                      | Sarvam LLM / RAG  |
                                                      +-------------------+
```

### Core Architectural Principles
1. **Strict Adapter Isolation:** Every external API lives in its own module inside `backend/integrations/` inheriting a common `BaseIntegrationClient` (`httpx` timeouts, exponential backoff retries, rate-limit `429` handling, TTL caching, structured validation, redacted logging, and explicit configuration checks).
2. **Per-Farmer Authorization:** Every authenticated query filters strictly by `current_farmer.id`. One farmer can never read, modify, or delete another farmer's profile, soil cards, crops, disease scans, profit scenarios, or voice history.
3. **Honest Degraded States:** Missing credentials or unavailable external services return structured `{ status: "not_configured" | "unavailable", configured: false, ... }` metadata and display visible status badges in the UI. No fake weather alerts, fake mandi prices, fake AI diagnoses, or unverified fertilizer prices are ever presented as real data.
4. **Logo Policy:** The UI references `/assets/raithamitra-logo.png` directly inside `frontend/public/assets/`. Until the original PNG is placed there, the `BrandLogo` component displays a clean neutral placeholder box without redesigning or substituting the logo.

---

## 2. Folder Structure

```text
C:\PROJECTS\raitha-mitra\
├── PLAN.md
├── README.md
├── .gitignore
├── docs\
│   ├── ENVIRONMENT_VARIABLES.md
│   ├── DEPLOYMENT.md
│   └── PHASE_REPORTS.md
├── tests\
│   └── integration_smoke.md
├── frontend\
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── public\
│   │   └── assets\                 # Place original raithamitra-logo.png here
│   └── src\
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── types\
│       ├── context\
│       ├── hooks\
│       ├── services\
│       │   └── api.ts
│       ├── components\
│       │   ├── common\
│       │   ├── layout\
│       │   └── voice\
│       └── pages\
└── backend\
    ├── .env.example
    ├── requirements.txt
    ├── alembic.ini
    ├── main.py
    ├── config.py
    ├── database.py
    ├── voice_agent.py              # LiveKit Agents worker (Sarvam Saaras + Bulbul)
    ├── alembic\
    │   ├── env.py
    │   └── versions\
    ├── models\
    ├── schemas\
    ├── routers\
    ├── services\
    ├── integrations\
    ├── utils\
    ├── data\                       # Verified local reference catalogs & optional downloaded SoilGrids/Bhuvan extracts
    ├── uploads\                    # Safe local file storage (soil cards, leaf photos)
    └── tests\                      # Pytest unit & API test suite
```

---

## 3. Modules & Routes (16 Modules)

| # | Route | Page Component | Backend Router |
|---|---|---|---|
| 1 | `/` | `LandingPage` | — (public) |
| 2 | `/auth` | `AuthPage` | `/api/v1/auth/*` |
| 3 | `/dashboard` | `DashboardPage` | `/api/v1/dashboard` |
| 4 | `/voice` | `VoiceAssistantPage` | `/api/v1/voice/*` (+ WS) |
| 5 | `/weather` | `WeatherPage` | `/api/v1/weather/*` |
| 6 | `/soil` | `SoilHealthPage` | `/api/v1/soil/*` |
| 7 | `/crops` | `CropRecommendationPage` | `/api/v1/crops/recommend` |
| 8 | `/growth` | `CropMonitoringPage` | `/api/v1/crops/monitoring/*` |
| 9 | `/pest-detection` | `PestDetectionPage` | `/api/v1/pests/*` |
| 10 | `/fertilizer` | `FertilizerPage` | `/api/v1/fertilizer/*` |
| 11 | `/yield` | `YieldPredictionPage` | `/api/v1/yield/*` |
| 12 | `/nutrition` | `NutritionPage` | `/api/v1/nutrition/*` |
| 13 | `/mandi` | `MandiPage` | `/api/v1/mandi/*` |
| 14 | `/profit` | `ProfitCalculatorPage` | `/api/v1/profit/*` |
| 15 | `/schemes` | `SchemesPage` | `/api/v1/schemes/*` |
| 16 | `/profile` | `ProfilePage` | `/api/v1/farmers/me` |

---

## 4. External Integration Verification & Status Table

| Integration | Purpose | Official Source / Verified Endpoint | Auth / Approval Needed | Verification & Implementation Status |
|---|---|---|---|---|
| **LiveKit (`livekit-agents[sarvam]`)** | Real-time WebRTC voice transport & barge-in room orchestration | `livekit.io` / PyPI `livekit-agents[sarvam]>=1.8.6,<2` + `livekit-api` | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (LiveKit Cloud or self-hosted) | **Verified** — Token router + `voice_agent.py` worker implemented; shows `not configured` if env missing |
| **Sarvam AI (Saaras STT, Bulbul TTS, Sarvam-105b LLM)** | Multilingual Indian voice STT (`saaras:v4`/`v3-realtime`), TTS (`bulbul:v4-flash`/`v3`), chat (`/v2`) | `https://api.sarvam.ai` (`api-subscription-key`, BCP-47 `kn-IN`, `hi-IN`, `te-IN`, `en-IN`, `ta-IN`, `mr-IN`) | `SARVAM_API_KEY` (paid/developer credits) | **Verified** — LiveKit Sarvam plugin + REST/WS fallback adapter implemented; shows `not configured` if key missing |
| **IMD (India Meteorological Department)** | Primary official source for district weather warnings & city forecasts | `https://api.imd.gov.in` (`POST /api/oauth/token.php`, `X-API-KEY` + Bearer JWT, `/api/v1/cityforecast`, district warnings) | `IMD_API_KEY`, `IMD_USERNAME`, `IMD_PASSWORD` + institutional registration & static server IP binding | **Partially Verified** — Portal & auth verified; exact per-endpoint warning payload fields depend on IMD Test Console access (`IMD_WARNINGS_PATH` configurable) |
| **OpenWeatherMap** | Fallback **forecasts only** (never warnings) | `https://api.openweathermap.org/data/2.5/weather` & `/data/2.5/forecast` (free tier) or `/data/3.0/onecall` | `OPENWEATHER_API_KEY` (free signup; One Call 3.0 needs card) | **Verified** — Adapter implemented strictly for fallback forecast only |
| **CWC (Central Water Commission)** | River flood levels & basin flood warnings | `https://ffs.india-water.gov.in` / India-WRIS | No public self-service REST API; requires institutional CWC/NWIC feed onboarding | **Verified Limitation (No Public API)** — Adapter reports `unavailable / institutional access required` unless `CWC_API_URL` & `CWC_API_KEY` are supplied; never fabricates flood alerts |
| **SoilGrids (ISRIC) & ISRO Bhuvan** | Downloadable soil dataset estimate fallback (NOT paused REST API) | `https://files.isric.org/soilgrids/latest/data/` (WebDAV/GeoTIFF/WCS) & `https://bhuvan.nrsc.gov.in/` | Local downloaded GeoTIFF/CSV extract path (`SOIL_DATASET_PATH`) or optional ISRIC WCS | **Verified** — Local dataset + WCS reader clearly marked `"ESTIMATED"` with confidence; lab values always override |
| **Soil Lab Card OCR** | Extract pH, N, P, K, OC, EC from PDF/JPG/PNG | Local `pypdf` + optional `rapidocr-onnxruntime` / Tesseract (`pytesseract`) | None locally (optional Vision OCR key if configured) | **Verified** — Safe upload + parser + mandatory review-and-correct workflow |
| **Plantix Intelligence API** | Primary crop pest & disease image detection | `https://b2b.plantix.net` (Stoplight docs: `POST /v1/image-analysis`) | Commercial B2B partner contract (`PLANTIX_API_KEY`, `PLANTIX_BASE_URL`) | **Partially Verified (Partner-Gated)** — Adapter matches Stoplight spec (`image`, `crop`, `latitude`, `longitude`); partner host URL confirmed upon onboarding; defaults to `not configured` |
| **Fallback Disease Vision Interface** | Pluggable image classifier fallback when Plantix unavailable | OpenAI/Gemini-compatible multimodal endpoint (`VISION_MODEL_BASE_URL`, `VISION_MODEL_API_KEY`) | `VISION_MODEL_API_KEY` | **Verified Interface** — Pluggable adapter; reports `not configured` when no key is set |
| **Google Agricultural Understanding (`ALU` / `AMED`)** | Field boundary, water bodies, crop history, sowing & harvest dates | `https://agriculturalunderstanding.googleapis.com` (`POST /v1:lookupLandscape`, `lookupLandscapeCaptureDate`, `monitorLandscape`) | `GOOGLE_AGRI_API_KEY` / GCP Cloud enablement | **Verified Scope** — **Does NOT offer a yield prediction endpoint**; used only as optional field/sowing metadata enrichment alongside our modular agronomic yield engine |
| **USDA FoodData Central** | Established food composition & micronutrient data | `https://api.nal.usda.gov/fdc/v1/foods/search` & `/food/{fdcId}` | `USDA_FDC_API_KEY` (free `api.data.gov` signup) | **Verified** — Adapter implemented with rate-limit header handling |
| **NCBI PubMed E-utilities** | Preliminary agricultural/nutritional research literature | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` & `esummary.fcgi` (`retmode=json`) | Optional `NCBI_API_KEY` (3 req/s without key, 10 req/s with key) | **Verified** — Adapter implemented with tool/email attribution |
| **ICMR-NIN (IFCT 2017) & FAO/INFOODS** | Indian food composition values & component tagnames | NIN IFCT 2017 publications & FAO INFOODS guidelines | No official live REST API | **Verified Limitation (No Public API)** — Curated verified reference JSON dataset with explicit citations |
| **data.gov.in AGMARKNET** | Daily mandi wholesale commodity prices | `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070` | `DATA_GOV_IN_API_KEY` (free registration) | **Verified** — Adapter implemented; labelled `"Latest Available Daily Data"` |
| **CEDA Agmarknet API** | Cleaned historical & daily Agmarknet prices & arrivals | `https://api.ceda.ashoka.edu.in/v1` (`/agmarknet/commodities`, `/geographies`, `/markets`, `/prices`, `/quantities`) | `CEDA_API_KEY` (free academic/non-commercial signup) | **Verified Endpoints** — Exact auth header configurable via `CEDA_AUTH_HEADER` (`x-api-key` / `Bearer`) |
| **e-NAM** | Electronic National Agriculture Market live portal | `https://www.enam.gov.in` | No official public self-service REST API documented | **Unverified Public API** — Marked portal-only / optional partner endpoint (`ENAM_API_URL`) |
| **API Setu myScheme & data.gov.in Schemes** | Official central/state welfare & agricultural schemes | `https://apisetu.gov.in/dic/myscheme` & `api.data.gov.in` | `APISETU_API_KEY` / `DATA_GOV_IN_API_KEY` | **Verified** — Adapter implemented + curated official `.gov.in` scheme registry with `last_verified` timestamps |
| **Fertilizer Price / MRP Feed** | Verified fertilizer prices by pack & subsidy MRP | Optional `FERTILIZER_PRICE_API_URL` | `FERTILIZER_PRICE_API_KEY` (no universal free national live dealer API) | **Unverified / Unavailable by default** — Displays `Price unavailable` unless a verified dated source is configured |

---

## 5. Phased Execution Plan

1. **Phase 1 — Foundation:** Project config, `.env.example`, database setup (SQLAlchemy + Alembic), models, Pydantic schemas, JWT auth, security utilities (rate limiting, file upload guards, per-farmer authorization), typed frontend API client & auth context.
2. **Phase 2 — Design & Shell:** Tailwind tokens matching exact color palette, `BrandLogo` with gentle growing-leaf Framer Motion animation and neutral placeholder fallback, responsive mobile-first navigation shell, Landing Page (`/`), Auth/Profile onboarding (`/auth`), Dashboard (`/dashboard`), and Profile/Settings (`/profile`).
3. **Phase 3 — Core Agriculture:** Weather & Flood (`/weather`), Soil Health OCR + lab review + local dataset estimates (`/soil`), Crop Recommendation incl. vegetables & fruits (`/crops`), Crop Growth Monitoring (`/growth`), Pest & Disease Detection with Plantix + pluggable fallback (`/pest-detection`), Fertilizer Recommendations (`/fertilizer`).
4. **Phase 4 — Intelligence:** Yield & Harvest Prediction + Google ALU/AMED adapter (`/yield`), Nutrition & Utilization with ICMR-NIN / USDA FDC / FAO INFOODS / PubMed (`/nutrition`), Mandi Prices (`/mandi`), Profit Calculator (`/profit`), Government Schemes (`/schemes`).
5. **Phase 5 — Voice (Highest Priority):** LiveKit token service + LiveKit Agents Sarvam worker (`Saaras` STT + `Bulbul` TTS + `Sarvam-105b`), multilingual WebSocket/REST streaming pipeline, immediate interruption/barge-in handling, persistent farmer-context injection (`profile + soil + weather + crop stage`), and UI with waveform, transcripts, and missing-data prompts.
6. **Phase 6 — Integration, Testing & Verification:** End-to-end backend `pytest` unit + API + security isolation tests, frontend TypeScript typecheck & production Vite build, responsive checks, documentation (`README.md`, `docs/*`), and honest verification report.
