@echo off
echo ==============================================================================
echo Starting ModelOps Studio (FastAPI Backend + Next.js Frontend)
echo ==============================================================================

echo [1/2] Launching FastAPI Backend on http://localhost:8000 ...
start "ModelOps Studio - API" cmd /k "call .venv\Scripts\activate.bat && uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Next.js Frontend on http://localhost:3000 ...
start "ModelOps Studio - Web" cmd /k "cd apps\web && npm run dev"

echo.
echo Both servers started!
echo Frontend: http://localhost:3000
echo Backend API Docs: http://localhost:8000/docs
echo ==============================================================================
