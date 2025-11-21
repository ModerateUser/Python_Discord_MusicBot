@echo off
REM Discord Music Bot - Basic Launcher
REM Launches the bot without web dashboard

echo ========================================
echo Discord Music Bot - Basic Launcher
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

REM Check if config.json exists
if not exist "config.json" (
    echo ERROR: config.json not found!
    echo.
    echo Please create config.json from config.example.json:
    echo   1. Copy config.example.json to config.json
    echo   2. Edit config.json and add your Discord bot token
    echo   3. Configure other settings as needed
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
python -c "import discord" >nul 2>&1
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

REM Launch the bot
echo Starting Discord Music Bot...
echo Press Ctrl+C to stop the bot
echo.
python bot.py

REM If bot exits with error
if errorlevel 1 (
    echo.
    echo ========================================
    echo Bot stopped with an error
    echo Check the logs above for details
    echo ========================================
    pause
    exit /b 1
)

echo.
echo Bot stopped normally
pause
