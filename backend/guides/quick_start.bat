@echo off
echo ========================================
echo Voice Assistant - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  WARNING: .env file not found!
    echo Please copy .env.example to .env and add your Gemini API key
    echo.
    pause
    exit /b
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt
echo.

REM Initialize database
echo Initializing database...
python -c "from app.database import init_db; from app.config import create_directories; create_directories(); init_db()"
echo.

REM Start server
echo ========================================
echo Starting Voice Assistant Server...
echo ========================================
echo.
echo 📡 Server will be available at: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload
