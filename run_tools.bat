@echo off
title GT-POS Database Tools
echo ========================================
echo   GT-POS Manager - Database Tools
echo ========================================
echo.
echo  This tool will help you:
echo  - Connect to SQL Server
echo  - Create/Update the database
echo  - Backup and restore data
echo  - Merge schema without data loss
echo.
cd /d "%~dp0Tools"
python db_tool.py
pause