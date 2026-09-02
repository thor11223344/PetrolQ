@echo off
echo ===================================================
echo   Starting eRTMAC-NWIS Backend and Frontend
echo ===================================================

echo.
echo [1/4] Installing Backend Dependencies...
python -m pip install -r requirements.txt

echo.
echo [2/4] Installing Frontend Dependencies...
cd frontend
call npm install
cd ..

echo.
echo [3/4] Starting Backend (FastAPI)...
start cmd /k "python -m uvicorn backend.main:app --reload --port 8000"

echo.
echo [4/4] Starting Frontend (Vite)...
start cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   Servers are starting in new windows!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo ===================================================
pause
