@echo off
title eRTMAC-NWIS Launcher
echo ===================================================
echo   Starting eRTMAC-NWIS (Backend + Frontend)
echo ===================================================
echo.
echo Starting FastAPI Backend on http://localhost:8000 ...
start "eRTMAC Backend (:8000)" cmd /k "python -m uvicorn backend.main:app --reload --port 8000"

echo Starting Vite Frontend on http://localhost:5173 ...
start "eRTMAC Frontend (:5173)" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   Both servers are launching in separate windows!
echo   - Frontend: http://localhost:5173
echo   - Backend:  http://localhost:8000
echo ===================================================
echo You can close this window now.
timeout /t 5 >nul
