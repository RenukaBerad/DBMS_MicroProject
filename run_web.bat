@echo off
title Internal Marks Management System - Web Dashboard Launcher
cd /d "%~dp0"

echo =====================================================================
echo  Internal Marks Management System - Web Dashboard
echo  College DBMS Micro-Project
echo =====================================================================
echo.
echo Launching Flask Web Server...
start "" http://127.0.0.1:5000
python server.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTICE] Web server stopped or exited with an error code.
    pause
)
