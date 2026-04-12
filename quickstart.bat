@echo off
REM ============================================================
REM AI Trading Platform - Quick Start Script (Windows)
REM ============================================================

setlocal enabledelayedexpansion

echo ============================================================
echo AI Trading Platform - Quick Setup (Windows)
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

echo OK: Python found
echo.

REM Navigate to backend directory
cd backend

REM Create virtual environment
echo Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo OK: Virtual environment created
) else (
    echo OK: Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo OK: Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo OK: Dependencies installed
echo.

REM Check for .env file
if not exist ".env" (
    echo Warning: .env file not found
    echo.
    echo Creating .env template...
    (
        echo # Claude AI Configuration
        echo CLAUDE_API_KEY=your_claude_api_key_here
        echo CLAUDE_MODEL=claude-3-5-sonnet-20241022
        echo.
        echo # Groww API Configuration
        echo GROWW_API_KEY=your_groww_api_key
        echo GROWW_API_SECRET=your_groww_api_secret
        echo GROWW_AUTH_TOKEN=your_groww_auth_token
        echo GROWW_API_BASE_URL=https://api.groww.in
        echo.
        echo # Trading Configuration
        echo PAPER_TRADING_INITIAL_CAPITAL=100000
        echo LIVE_TRADING_ENABLED=false
        echo TRADING_SLIPPAGE_PERCENT=0.05
        echo TRADING_COMMISSION_PERCENT=0.02
        echo.
        echo # Database
        echo DATABASE_URL=sqlite:///./trading.db
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo.
        echo # App Configuration
        echo APP_NAME=AI Trading Platform
        echo APP_VERSION=1.0.0
        echo DEBUG=false
    ) > .env
    echo OK: .env template created
    echo.
    echo IMPORTANT: Edit .env with your API credentials
    echo You can open it with: notepad .env
    echo.
    echo Required credentials:
    echo - CLAUDE_API_KEY: Get from https://console.anthropic.com
    echo - GROWW_API_KEY, GROWW_API_SECRET, GROWW_AUTH_TOKEN
    echo.
) else (
    echo OK: .env file found
)

echo.
echo ============================================================
echo OK: Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Configure your API keys in .env
echo    notepad .env
echo.
echo 2. Run the platform:
echo.
echo    python main.py
echo.
echo 3. Open in browser:
echo.
echo    - API Documentation: http://localhost:8000/docs
echo    - ReDoc: http://localhost:8000/redoc
echo    - Health Check: http://localhost:8000/health
echo.
echo For detailed setup instructions, see: SETUP_GUIDE.md
echo.
echo ============================================================
echo.
pause
