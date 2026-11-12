# Raitha Mitra — Your Smart Farming Companion

Raitha Mitra is a mobile-first, multilingual AI farming platform built for Indian farmers with React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy/Alembic, LiveKit Agents, and Sarvam AI.

## Project Structure

- `frontend/` — React + TypeScript + Vite + Tailwind CSS + Framer Motion + Recharts + Lucide React (`src/pages/`, `src/components/`, `src/services/api.ts`, `src/hooks/`, `src/context/`, `src/types/`)
- `backend/` — Python + FastAPI + Pydantic + SQLAlchemy + Alembic (`routers/`, `services/`, `integrations/`, `models/`, `schemas/`, `utils/`, `voice_agent.py`)
- `docs/` — Environment variable reference & deployment instructions
- `tests/` — Pytest unit and API integration tests
- `PLAN.md` — Full architecture, folder map, and honest external API verification table

## Quick Start

### 1. Place Brand Logo
Copy your original PNG logo to:
`frontend/public/assets/raithamitra-logo.png`

### 2. Backend Setup
```powershell
cd C:\PROJECTS\raitha-mitra\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```powershell
cd C:\PROJECTS\raitha-mitra\frontend
npm install
npm run dev
```

### 4. Run Tests
```powershell
cd C:\PROJECTS\raitha-mitra\backend
pytest
```
