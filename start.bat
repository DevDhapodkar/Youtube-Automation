@echo off
setlocal

:: Configuration Check
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please run: python setup.py
    pause
    exit /b 1
)

echo 🚀 Starting YouTube Automation Agent...

:: Start Backend
echo [BACKEND] Starting Services...
set PYTHONPATH=%PYTHONPATH%;%CD%
start "YouTube Agent Backend" cmd /c "venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000"

:: Start Frontend
echo [FRONTEND] Starting Web UI...
if exist "web" (
    cd web
    start "YouTube Agent Frontend" cmd /c "npm run dev"
    cd ..
) else (
    echo [WARNING] 'web' directory not found. Frontend not started.
)

echo.
echo ✅ Full stack is booting up.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause
