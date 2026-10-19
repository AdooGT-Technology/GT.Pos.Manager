@echo off
title GT-POS Gizmo Manager Setup
color 0b
cd /d "%~dp0"
echo ====================================================
echo      GT-POS Gizmo Manager Auto Setup
echo ====================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed. Please install Python 3.10+
    pause
    exit
)

:: 2. Install Requirements
echo [*] Installing dependencies...
pip install pyodbc PyQt6
echo.

:: 3. Run DB Tool to Create/Migrate Database
echo [*] Setting up and repairing database [GT-POS-Manager]...
set PYTHONPATH=.
python setup_db.py
echo.

echo [SUCCESS] Setup complete! 
echo You can now run 'run_manager.bat' to start the application.
pause