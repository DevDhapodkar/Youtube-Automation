@echo off
echo Starting YouTube Automation Agent...

:: Start Backend
echo Starting Backend...
set PYTHONPATH=%PYTHONPATH%;%CD%
start "Backend" cmd /c "venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000"

:: Start Frontend
echo Starting Frontend...
cd web
start "Frontend" cmd /c "npm run dev"

echo.
echo Both Backend and Frontend are starting in separate windows.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause
