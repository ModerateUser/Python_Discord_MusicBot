@echo off
title Discord Music Bot - Integrated System (Bot + Dashboard)
color 0E

echo ========================================
echo   Discord Music Bot - Integrated Mode
echo ========================================
echo   Bot + Dashboard in Same Process
echo   Real-time Communication Enabled
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

REM Check if venv exists and is valid
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
    echo Creating template config.json from config.example.json...
    
    if exist "config.example.json" (
        copy "config.example.json" "config.json" >nul
        echo [SUCCESS] config.json created from example template
        echo [INFO] Please edit config.json with your bot token and owner ID
    ) else (
        echo [WARNING] config.example.json not found, generating complete template...
        (
            echo {
            echo     "token": "YOUR_BOT_TOKEN_HERE",
            echo     "owner_id": 123456789012345678,
            echo     "playing": "!help for commands",
            echo     "command_prefix": "!",
            echo     "max_queue_size": 100,
            echo     "max_playlist_size": 500,
            echo     "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"],
            echo     "music_directory": null,
            echo     "llm": {
            echo         "enabled": false,
            echo         "provider": "ollama",
            echo         "model": "llama3",
            echo         "api_key": null,
            echo         "base_url": "http://localhost:11434",
            echo         "timeout": 30,
            echo         "max_tokens": 500
            echo     },
            echo     "music_synthesis": {
            echo         "enabled": false,
            echo         "backend": "disabled",
            echo         "cache_dir": "generated_music",
            echo         "max_cache_size_mb": 1000,
            echo         "default_duration": 30,
            echo         "default_quality": "medium",
            echo         "suno_api_key": null,
            echo         "suno_api_url": "https://api.suno.ai/v1",
            echo         "musicgen_model": "facebook/musicgen-small"
            echo     },
            echo     "web_dashboard": {
            echo         "enabled": true,
            echo         "host": "0.0.0.0",
            echo         "port": 8000
            echo     }
            echo }
        ) > config.json
        echo [SUCCESS] config.json created with complete template
        echo [INFO] Please edit config.json with your bot token and owner ID
    )
    echo.
    echo IMPORTANT: Edit config.json and set:
    echo   - token: Your Discord bot token
    echo   - owner_id: Your Discord user ID ^(as a number^)
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
echo   Starting Integrated System
echo ========================================
echo.
echo [INFO] Bot and Dashboard will run together
echo [INFO] Real-time communication enabled
echo.
echo Dashboard URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the system
echo ========================================
echo.

REM Wait a moment before opening browser
timeout /t 2 /nobreak >nul

REM Open browser to dashboard
start http://localhost:8000

REM Start the integrated system
echo [INFO] Starting integrated bot + dashboard...
echo ========================================
echo.
python bot_with_dashboard.py

REM Handle errors
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] System stopped with an error
    echo ========================================
    echo.
    echo Check logs/bot.log for details
    echo.
    echo Common issues:
    echo   - Invalid bot token in config.json
    echo   - Port 8000 already in use
    echo   - Missing dependencies
    echo   - FFmpeg not installed
)

echo.
echo [INFO] System stopped.
pause