@echo off
title Discord Music Bot - Update Dependencies
color 0B

echo ========================================
echo   Update Bot Dependencies
echo ========================================
echo.

REM Activate virtual environment
if exist "venv\" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found
    echo Please run launch.bat first to create it
    pause
    exit /b 1
)

echo [INFO] Updating pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Updating dependencies...
pip install --upgrade -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to update dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] All dependencies updated!
echo ========================================
echo.
pause