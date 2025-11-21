@echo off
title Discord Music Bot Launcher
color 0A

echo ========================================
echo   Discord Music Bot Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Check if venv exists
if not exist "venv\" (
    echo [SETUP] Virtual environment not found. Creating...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if config.json exists
if not exist "config.json" (
    echo [WARNING] config.json not found!
    echo Please create config.json with your bot token
    echo.
    echo Creating template config.json...
    (
        echo {
        echo     "token": "YOUR_BOT_TOKEN_HERE",
        echo     "owner_id": "YOUR_DISCORD_USER_ID_HERE",
        echo     "playing": "!help for commands"
        echo }
    ) > config.json
    echo [INFO] Template config.json created. Please edit it with your details.
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo [INFO] Checking dependencies...
python -c "import discord, yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing/updating dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
    echo.
)

REM Check for FFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found in PATH
    echo The bot may not be able to play audio without FFmpeg
    echo Download from: https://ffmpeg.org/download.html
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
    echo.
)

REM Run the bot
echo [INFO] Starting Discord Music Bot...
echo ========================================
echo.
python bot.py

REM Handle errors
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Bot stopped with an error
    echo ========================================
)

echo.
pause
