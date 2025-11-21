@echo off
title Discord Music Bot - Complete System Launcher
color 0E

echo ========================================
echo   Discord Music Bot - Complete System
echo ========================================
echo   Bot + Web Dashboard
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

REM FIX LAUNCH #3: Check if venv exists and is valid
set "USE_VENV=0"
if exist "venv\Scripts\python.exe" (
    echo [INFO] Virtual environment found
    set "USE_VENV=1"
) else if exist "venv\" (
    echo [WARNING] venv folder exists but is incomplete/corrupted
    echo [INFO] Removing incomplete venv...
    rmdir /s /q "venv"
)

REM Create venv if it doesn't exist
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [WARNING] Failed to create virtual environment
        echo [INFO] Will run without venv (using system Python)
        set "USE_VENV=0"
    ) else (
        echo [SUCCESS] Virtual environment created
        set "USE_VENV=1"
    )
    echo.
)

REM Activate virtual environment if available
if "%USE_VENV%"=="1" (
    if exist "venv\Scripts\activate.bat" (
        echo [INFO] Activating virtual environment...
        call venv\Scripts\activate.bat
        if errorlevel 1 (
            echo [WARNING] Failed to activate venv, using system Python
            set "USE_VENV=0"
        )
    ) else (
        echo [WARNING] venv\Scripts\activate.bat not found
        echo [INFO] Using system Python instead
        set "USE_VENV=0"
    )
) else (
    echo [INFO] Using system Python (no venv)
)

echo.

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
        echo     "command_prefix": "!",
        echo     "playing": "!help for commands",
        echo     "max_queue_size": 100,
        echo     "max_playlist_size": 500,
        echo     "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"],
        echo     "music_directory": null,
        echo     "llm": {
        echo         "enabled": false,
        echo         "provider": "openai",
        echo         "model": "gpt-3.5-turbo",
        echo         "api_key": null
        echo     },
        echo     "music_synthesis": {
        echo         "enabled": false,
        echo         "backend": "disabled"
        echo     }
        echo }
    ) > config.json
    echo [INFO] Template config.json created. Please edit it with your details.
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo [INFO] Checking dependencies...
python -c "import discord, yt_dlp, fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing/updating dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        echo Try running manually:
        echo   pip install -r requirements.txt
        echo.
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
)

REM Create necessary directories
if not exist "logs\" mkdir logs
if not exist "web_dashboard\static\" (
    mkdir "web_dashboard\static"
    mkdir "web_dashboard\static\css"
    mkdir "web_dashboard\static\js"
)
if not exist "web_dashboard\templates\" (
    mkdir "web_dashboard\templates"
)

echo ========================================
echo   Starting Discord Music Bot System
echo ========================================
echo.
echo [1] Bot will start in this window
echo [2] Web Dashboard will open in a new window
echo.
echo Dashboard URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C in either window to stop
echo ========================================
echo.

REM FIX LAUNCH #3: Start dashboard with proper venv handling
if "%USE_VENV%"=="1" (
    start "Discord Bot - Web Dashboard" cmd /k "call venv\Scripts\activate.bat && cd web_dashboard && python app.py"
) else (
    start "Discord Bot - Web Dashboard" cmd /k "cd web_dashboard && python app.py"
)

REM Wait a moment for dashboard to start
timeout /t 3 /nobreak >nul

REM Open browser to dashboard
start http://localhost:8000

REM Start the bot in this window
echo [INFO] Starting Discord Bot...
echo ========================================
echo.
python bot.py

REM Handle errors
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Bot stopped with an error
    echo ========================================
    echo.
    echo Check logs/bot.log for details
)

echo.
echo [INFO] Bot stopped. Dashboard may still be running in the other window.
echo [INFO] Close the dashboard window to fully stop the system.
pause
