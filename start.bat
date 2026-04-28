@echo off
echo Starting Stock Reversal Analyzer...

:: Start backend
cd /d "%~dp0backend"
if not exist ".env" (
    copy ".env.example" ".env"
    echo Created .env from .env.example - please add your Claude API key
)
start "Backend" cmd /k "python -m uvicorn app.main:app --reload --port 8000"

:: Start frontend
cd /d "%~dp0frontend"
start "Frontend" cmd /k "npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
