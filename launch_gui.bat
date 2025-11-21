@echo off
title Discord Music Bot - Web Dashboard Launcher
color 0B

echo ========================================
echo   Discord Music Bot - Web Dashboard
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

REM FIX LAUNCH #2: Check if venv exists and is valid
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
    echo The dashboard will still work, but bot integration requires config.json
    echo.
)

REM Check if FastAPI dependencies are installed
echo [INFO] Checking dashboard dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dashboard dependencies...
    python -m pip install --upgrade pip
    pip install fastapi uvicorn[standard] jinja2 python-multipart websockets
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        echo Try running manually:
        echo   pip install fastapi uvicorn[standard] jinja2 python-multipart websockets
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed
    echo.
)

REM Check if templates directory exists
if not exist "web_dashboard\templates\" (
    echo [INFO] Creating templates directory...
    mkdir "web_dashboard\templates"
)

REM Create static directory if it doesn't exist
if not exist "web_dashboard\static\" (
    echo [INFO] Creating static directory...
    mkdir "web_dashboard\static"
    mkdir "web_dashboard\static\css"
    mkdir "web_dashboard\static\js"
)

REM Run the dashboard
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

cd web_dashboard
python app.py

REM Handle errors
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Dashboard stopped with an error
    echo ========================================
    echo.
    echo Check the error message above for details
)

echo.
pause
