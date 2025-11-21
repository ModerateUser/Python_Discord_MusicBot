@echo off
title Discord Music Bot - Unified Launcher
color 0A

:MENU
cls
echo ========================================
echo   Discord Music Bot - Unified Launcher
echo ========================================
echo.
echo Select Launch Mode:
echo.
echo   [1] Bot Only (Discord Bot)
echo   [2] Dashboard Only (Web Interface)
echo   [3] Integrated Mode (Bot + Dashboard)
echo   [4] Separate Windows (Bot + Dashboard)
echo.
echo   [5] Install/Update Dependencies
echo   [6] Check System Requirements
echo   [7] Create/Reset Config File
echo.
echo   [0] Exit
echo.
echo ========================================
echo.

choice /C 123456780 /N /M "Enter your choice: "
set CHOICE=%ERRORLEVEL%

if "%CHOICE%"=="1" goto BOT_ONLY
if "%CHOICE%"=="2" goto DASHBOARD_ONLY
if "%CHOICE%"=="3" goto INTEGRATED
if "%CHOICE%"=="4" goto SEPARATE
if "%CHOICE%"=="5" goto INSTALL_DEPS
if "%CHOICE%"=="6" goto CHECK_SYSTEM
if "%CHOICE%"=="7" goto CREATE_CONFIG
if "%CHOICE%"=="9" goto EXIT

goto MENU

REM ============================================================================
REM COMMON SETUP FUNCTIONS
REM ============================================================================

:SETUP_ENVIRONMENT
REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

REM Set explicit paths for venv executables
set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
set "VENV_PIP=%~dp0venv\Scripts\pip.exe"
set "USE_VENV=0"

REM Check if venv exists and is valid
if exist "%VENV_PYTHON%" (
    echo [INFO] Virtual environment found
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

REM If no venv, use system Python
if "%USE_VENV%"=="0" (
    echo [INFO] Using system Python
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

echo [INFO] Python executable: %PYTHON_CMD%
"%PYTHON_CMD%" --version
echo.

exit /b 0

:CHECK_CONFIG
REM Check if config.json exists
if not exist "config.json" (
    echo [WARNING] config.json not found!
    echo.
    choice /C YN /M "Create config.json from template"
    if errorlevel 2 exit /b 1
    
    if exist "config.example.json" (
        copy "config.example.json" "config.json" >nul
        echo [SUCCESS] config.json created from example template
    ) else (
        call :GENERATE_CONFIG
    )
    echo.
    echo IMPORTANT: Edit config.json and set:
    echo   - token: Your Discord bot token
    echo   - owner_id: Your Discord user ID (as a number)
    echo.
    pause
    exit /b 1
)
exit /b 0

:GENERATE_CONFIG
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
exit /b 0

:CHECK_DEPENDENCIES
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
        echo   %PIP_CMD% install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
    echo.
)
exit /b 0

:CHECK_DASHBOARD_DEPENDENCIES
echo [INFO] Checking dashboard dependencies...
"%PYTHON_CMD%" -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dashboard dependencies...
    "%PYTHON_CMD%" -m pip install --upgrade pip
    "%PIP_CMD%" install fastapi uvicorn[standard] jinja2 python-multipart websockets
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [SUCCESS] Dashboard dependencies installed
    echo.
)
exit /b 0

:CHECK_FFMPEG
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found in PATH
    echo The bot may not be able to play audio without FFmpeg
    echo Download from: https://ffmpeg.org/download.html
    echo.
    choice /C YN /M "Continue anyway"
    if errorlevel 2 exit /b 1
)
exit /b 0

:CREATE_DIRECTORIES
if not exist "logs\" mkdir logs
if not exist "web_dashboard\templates\" mkdir "web_dashboard\templates"
if not exist "web_dashboard\static\" (
    mkdir "web_dashboard\static"
    mkdir "web_dashboard\static\css"
    mkdir "web_dashboard\static\js"
)
exit /b 0

REM ============================================================================
REM LAUNCH MODE 1: BOT ONLY
REM ============================================================================

:BOT_ONLY
cls
echo ========================================
echo   Discord Music Bot - Bot Only Mode
echo ========================================
echo.

call :SETUP_ENVIRONMENT
if errorlevel 1 goto MENU

call :CHECK_CONFIG
if errorlevel 1 goto MENU

call :CHECK_DEPENDENCIES
if errorlevel 1 goto MENU

call :CHECK_FFMPEG
if errorlevel 1 goto MENU

call :CREATE_DIRECTORIES

echo [INFO] Starting Discord Music Bot...
echo ========================================
echo.

"%PYTHON_CMD%" bot.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Bot stopped with an error
    echo ========================================
    echo Check logs/bot.log for details
)

echo.
pause
goto MENU

REM ============================================================================
REM LAUNCH MODE 2: DASHBOARD ONLY
REM ============================================================================

:DASHBOARD_ONLY
cls
echo ========================================
echo   Discord Music Bot - Dashboard Only
echo ========================================
echo.

call :SETUP_ENVIRONMENT
if errorlevel 1 goto MENU

call :CHECK_DASHBOARD_DEPENDENCIES
if errorlevel 1 goto MENU

call :CREATE_DIRECTORIES

echo [INFO] Starting Web Dashboard...
echo ========================================
echo.
echo Dashboard will be available at:
echo   http://localhost:8000
echo.
echo API Documentation:
echo   http://localhost:8000/docs
echo.
echo Health Check:
echo   http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the dashboard
echo ========================================
echo.

REM Wait a moment before opening browser
timeout /t 2 /nobreak >nul
start http://localhost:8000

cd web_dashboard
"%PYTHON_CMD%" app.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Dashboard stopped with an error
    echo ========================================
)

cd ..
echo.
pause
goto MENU

REM ============================================================================
REM LAUNCH MODE 3: INTEGRATED MODE
REM ============================================================================

:INTEGRATED
cls
echo ========================================
echo   Discord Music Bot - Integrated Mode
echo ========================================
echo   Bot + Dashboard in Same Process
echo   Real-time Communication Enabled
echo ========================================
echo.

call :SETUP_ENVIRONMENT
if errorlevel 1 goto MENU

call :CHECK_CONFIG
if errorlevel 1 goto MENU

call :CHECK_DEPENDENCIES
if errorlevel 1 goto MENU

call :CHECK_DASHBOARD_DEPENDENCIES
if errorlevel 1 goto MENU

call :CHECK_FFMPEG
if errorlevel 1 goto MENU

call :CREATE_DIRECTORIES

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
start http://localhost:8000

echo [INFO] Starting integrated bot + dashboard...
echo ========================================
echo.

"%PYTHON_CMD%" bot_with_dashboard.py

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
goto MENU

REM ============================================================================
REM LAUNCH MODE 4: SEPARATE WINDOWS
REM ============================================================================

:SEPARATE
cls
echo ========================================
echo   Discord Music Bot - Separate Windows
echo ========================================
echo   Bot + Dashboard in Separate Processes
echo ========================================
echo.

call :SETUP_ENVIRONMENT
if errorlevel 1 goto MENU

call :CHECK_CONFIG
if errorlevel 1 goto MENU

call :CHECK_DEPENDENCIES
if errorlevel 1 goto MENU

call :CHECK_DASHBOARD_DEPENDENCIES
if errorlevel 1 goto MENU

call :CHECK_FFMPEG
if errorlevel 1 goto MENU

call :CREATE_DIRECTORIES

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

REM Start dashboard in new window
if "%USE_VENV%"=="1" (
    start "Discord Bot - Web Dashboard" cmd /k "title Discord Bot - Web Dashboard && color 0B && call venv\Scripts\activate.bat && cd web_dashboard && python app.py"
) else (
    start "Discord Bot - Web Dashboard" cmd /k "title Discord Bot - Web Dashboard && color 0B && cd web_dashboard && python app.py"
)

REM Wait for dashboard to start
timeout /t 3 /nobreak >nul

REM Open browser to dashboard
start http://localhost:8000

REM Start the bot in this window
echo [INFO] Starting Discord Bot...
echo ========================================
echo.

"%PYTHON_CMD%" bot.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Bot stopped with an error
    echo ========================================
    echo Check logs/bot.log for details
)

echo.
echo [INFO] Bot stopped. Dashboard may still be running in the other window.
echo [INFO] Close the dashboard window to fully stop the system.
pause
goto MENU

REM ============================================================================
REM UTILITY: INSTALL/UPDATE DEPENDENCIES
REM ============================================================================

:INSTALL_DEPS
cls
echo ========================================
echo   Install/Update Dependencies
echo ========================================
echo.

call :SETUP_ENVIRONMENT
if errorlevel 1 goto MENU

echo [INFO] Updating pip...
"%PYTHON_CMD%" -m pip install --upgrade pip

echo.
echo [INFO] Installing/updating all dependencies...
"%PIP_CMD%" install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    pause
    goto MENU
)

echo.
echo [SUCCESS] All dependencies installed/updated successfully!
echo.
pause
goto MENU

REM ============================================================================
REM UTILITY: CHECK SYSTEM REQUIREMENTS
REM ============================================================================

:CHECK_SYSTEM
cls
echo ========================================
echo   System Requirements Check
echo ========================================
echo.

REM Check Python
echo [CHECK] Python Installation:
python --version 2>&1
if errorlevel 1 (
    echo   [FAIL] Python not found
) else (
    echo   [OK] Python found
)
echo.

REM Check venv
echo [CHECK] Virtual Environment:
if exist "venv\Scripts\python.exe" (
    echo   [OK] Virtual environment exists
    venv\Scripts\python.exe --version
) else (
    echo   [WARN] Virtual environment not found
    echo   Will be created on first launch
)
echo.

REM Check FFmpeg
echo [CHECK] FFmpeg:
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo   [WARN] FFmpeg not found in PATH
    echo   Required for audio playback
    echo   Download: https://ffmpeg.org/download.html
) else (
    ffmpeg -version 2>&1 | findstr "ffmpeg version"
    echo   [OK] FFmpeg found
)
echo.

REM Check config
echo [CHECK] Configuration:
if exist "config.json" (
    echo   [OK] config.json exists
) else (
    echo   [WARN] config.json not found
    echo   Will be created on first launch
)
echo.

REM Check dependencies
echo [CHECK] Python Dependencies:
if exist "venv\Scripts\python.exe" (
    set "CHECK_PYTHON=venv\Scripts\python.exe"
) else (
    set "CHECK_PYTHON=python"
)

"%CHECK_PYTHON%" -c "import discord" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] discord.py not installed
) else (
    echo   [OK] discord.py installed
)

"%CHECK_PYTHON%" -c "import yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] yt-dlp not installed
) else (
    echo   [OK] yt-dlp installed
)

"%CHECK_PYTHON%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] fastapi not installed
) else (
    echo   [OK] fastapi installed
)

"%CHECK_PYTHON%" -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo   [WARN] uvicorn not installed
) else (
    echo   [OK] uvicorn installed
)

echo.
echo ========================================
echo   Check Complete
echo ========================================
echo.
echo If any items show [WARN] or [FAIL], use option 5
echo to install/update dependencies.
echo.
pause
goto MENU

REM ============================================================================
REM UTILITY: CREATE/RESET CONFIG FILE
REM ============================================================================

:CREATE_CONFIG
cls
echo ========================================
echo   Create/Reset Config File
echo ========================================
echo.

if exist "config.json" (
    echo [WARNING] config.json already exists!
    echo.
    choice /C YN /M "Overwrite existing config.json"
    if errorlevel 2 goto MENU
    echo.
)

if exist "config.example.json" (
    echo [INFO] Copying from config.example.json...
    copy "config.example.json" "config.json" >nul
    echo [SUCCESS] config.json created from example template
) else (
    echo [INFO] Generating config.json template...
    call :GENERATE_CONFIG
)

echo.
echo [SUCCESS] config.json has been created!
echo.
echo IMPORTANT: Edit config.json and set:
echo   - token: Your Discord bot token
echo   - owner_id: Your Discord user ID (as a number)
echo.
echo Optional settings:
echo   - command_prefix: Bot command prefix (default: !)
echo   - llm.enabled: Enable AI features (requires Ollama/OpenAI)
echo   - music_synthesis.enabled: Enable music generation
echo   - web_dashboard: Dashboard settings
echo.
pause
goto MENU

REM ============================================================================
REM EXIT
REM ============================================================================

:EXIT
cls
echo.
echo Thank you for using Discord Music Bot!
echo.
timeout /t 2 /nobreak >nul
exit /b 0
