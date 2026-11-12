# Deployment Guide

## 1. Database (PostgreSQL Production)
1. Provision a PostgreSQL 15+ database and set `DATABASE_URL=postgresql+psycopg://user:password@host:5432/raithamitra` in backend environment variables.
2. Install `psycopg[binary]` alongside `backend/requirements.txt`.
3. Run Alembic migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```

## 2. Backend API (FastAPI + Uvicorn/Gunicorn)
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```
Set `APP_ENV=production`, a strong `SECRET_KEY`, and strict `CORS_ORIGINS` matching your deployed frontend origin.

## 3. Real-Time LiveKit + Sarvam Voice Worker
Run in a separate worker process/container using Python 3.10–3.13 with `livekit-agents[sarvam]>=1.8.6,<2`:
```bash
cd backend
python voice_agent.py start
```

## 4. Frontend (Vite Static Build)
```bash
cd frontend
npm run build
```
Serve `frontend/dist` behind Nginx, Caddy, or Vercel with `/api` proxied to the FastAPI backend (or set `VITE_API_BASE_URL` at build time).

## 5. Logo Asset
Ensure your original brand logo PNG is placed at:
`frontend/public/assets/raithamitra-logo.png`
