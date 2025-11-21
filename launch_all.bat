@echo off
REM Discord Music Bot - Interactive Launcher
REM Provides menu to choose launch mode

:MENU
cls
echo ========================================
echo Discord Music Bot - Launcher Menu
echo ========================================
echo.
echo Choose launch mode:
echo.
echo 1. Basic Bot (No Dashboard)
echo 2. Integrated Mode (Bot + Dashboard)
echo 3. Dashboard Only (Standalone)
echo 4. Exit
echo.
echo ========================================
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto BASIC
if "%choice%"=="2" goto INTEGRATED
if "%choice%"=="3" goto DASHBOARD
if "%choice%"=="4" goto EXIT

echo.
echo Invalid choice. Please enter 1, 2, 3, or 4.
timeout /t 2 >nul
goto MENU

:BASIC
echo.
echo Launching Basic Bot...
echo.
call launch.bat
goto END

:INTEGRATED
echo.
echo Launching Integrated Mode (Bot + Dashboard)...
echo.
call launch_integrated.bat
goto END

:DASHBOARD
echo.
echo Launching Dashboard Only...
echo.
call launch_gui.bat
goto END

:EXIT
echo.
echo Exiting launcher...
exit /b 0

:END
echo.
echo ========================================
echo.
set /p restart="Return to menu? (Y/N): "
if /i "%restart%"=="Y" goto MENU
if /i "%restart%"=="y" goto MENU
exit /b 0
