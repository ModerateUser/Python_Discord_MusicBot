@echo off
REM Discord Music Bot - Unified Launcher
REM Automatically detects and launches the bot with or without dashboard

echo ========================================
echo Discord Music Bot - Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

REM Check if config.json exists
if not exist "config.json" (
    echo WARNING: config.json not found
    echo Creating from config.example.json...
    if exist "config.example.json" (
        copy config.example.json config.json
        echo.
        echo Please edit config.json with your bot token and settings
        echo Then run this launcher again
        pause
        exit /b 1
    ) else (
        echo ERROR: config.example.json not found
        pause
        exit /b 1
    )
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import discord" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Select launch mode:
echo 1. Bot Only (Basic music bot)
echo 2. Bot + Dashboard (Integrated with web interface)
echo 3. Dashboard Only (Web interface standalone)
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Starting bot only...
    python bot.py
) else if "%choice%"=="2" (
    echo.
    echo Starting bot with integrated dashboard...
    python bot_with_dashboard.py
) else if "%choice%"=="3" (
    echo.
    echo Starting dashboard only...
    cd web_dashboard
    python -m uvicorn app:app --host 0.0.0.0 --port 8000
) else (
    echo Invalid choice. Defaulting to bot only...
    python bot.py
)

if errorlevel 1 (
    echo.
    echo ERROR: Bot crashed or failed to start
    echo Check the logs folder for error details
    pause
)
