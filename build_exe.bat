@echo off
echo 📦 Building YouTube Agent Executable...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: Create and activate virtual environment if it doesn't exist
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

echo ⬇️ Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

echo 🚀 Running PyInstaller...
pyinstaller yt_agent.spec --clean --noconfirm

echo.
echo ✅ Build complete!
echo 📂 Your executable is located in: dist/YouTubeAgent/YouTubeAgent.exe
echo.
pause
