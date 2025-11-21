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

REM Check if config.json exists
if not exist "config.json" (
    echo [WARNING] config.json not found!
    echo Please create config.json with your bot token
    echo.
    echo Creating template config.json from config.example.json...
    
    REM FIX CONFIG #1: Copy from example instead of generating inline
    if exist "config.example.json" (
        copy "config.example.json" "config.json" >nul
        echo [SUCCESS] config.json created from example template
        echo [INFO] Please edit config.json with your bot token and owner ID
    ) else (
        echo [WARNING] config.example.json not found, generating basic template...
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

REM FIX VENV #1: Set explicit paths for venv executables
set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
set "VENV_PIP=%~dp0venv\Scripts\pip.exe"
set "USE_VENV=0"

REM Check if venv exists and is valid
if exist "%VENV_PYTHON%" (
    echo [INFO] Virtual environment found: %VENV_PYTHON%
    set "USE_VENV=1"
    set "PYTHON_CMD=%VENV_PYTHON%"
    set "PIP_CMD=%VENV_PIP%"
) else if exist "venv\" (
    echo [WARNING] venv folder exists but python.exe not found
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
        set "PYTHON_CMD=python"
        set "PIP_CMD=pip"
    ) else (
        echo [SUCCESS] Virtual environment created
        REM Verify the venv was created properly
        if exist "%VENV_PYTHON%" (
            set "USE_VENV=1"
            set "PYTHON_CMD=%VENV_PYTHON%"
            set "PIP_CMD=%VENV_PIP%"
            echo [SUCCESS] Virtual environment validated
        ) else (
            echo [WARNING] venv created but python.exe not found
            set "USE_VENV=0"
            set "PYTHON_CMD=python"
            set "PIP_CMD=pip"
        )
    )
    echo.
)

REM FIX VENV #1: If no venv, use system Python
if "%USE_VENV%"=="0" (
    echo [INFO] Using system Python
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

echo.

REM FIX VENV #1: Display which Python is being used
echo [INFO] Python executable: %PYTHON_CMD%
"%PYTHON_CMD%" --version
echo.

REM Check if requirements are installed
echo [INFO] Checking dependencies...
"%PYTHON_CMD%" -c "import discord, yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing/updating dependencies...
    "%PYTHON_CMD%" -m pip install --upgrade pip
    "%PIP_CMD%" install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        echo Try running manually:
        if "%USE_VENV%"=="1" (
            echo   %PIP_CMD% install -r requirements.txt
        ) else (
            echo   pip install -r requirements.txt
        )
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
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
    echo.
)

REM Create logs directory if it doesn't exist
if not exist "logs\" mkdir logs

REM Run the bot
echo [INFO] Starting Discord Music Bot...
echo ========================================
echo.

REM FIX VENV #1: Use explicit Python path
"%PYTHON_CMD%" bot.py

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
pause
