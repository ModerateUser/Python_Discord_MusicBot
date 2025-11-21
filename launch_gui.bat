@echo off
REM Discord Music Bot - Dashboard Only Launcher
REM Launches web dashboard in standalone mode (without bot)

echo ========================================
echo Discord Music Bot - Dashboard Only
echo Web Interface (Standalone Mode)
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Dependencies not installed. Installing from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully!
    echo.
)

REM Launch the dashboard
echo ========================================
echo Starting Web Dashboard (Standalone Mode)
echo ========================================
echo.
echo NOTE: This mode runs the dashboard without the bot.
echo For full functionality, use launch_integrated.bat
echo.
echo Dashboard URL:
echo   http://localhost:8000
echo.
echo API Documentation:
echo   http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the dashboard
echo ========================================
echo.

cd web_dashboard
python app.py

REM If dashboard exits with error
if errorlevel 1 (
    echo.
    echo ========================================
    echo Dashboard stopped with an error
    echo Check the logs above for details
    echo ========================================
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo Dashboard stopped normally
pause
