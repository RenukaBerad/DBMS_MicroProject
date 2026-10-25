@echo off
title Internal Marks Management System - College DBMS Micro-Project
cd /d "%~dp0"

echo =====================================================================
echo  Internal Marks Management System
echo  College DBMS Micro-Project
echo =====================================================================
echo.
echo Checking Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in PATH.
    echo Please install Python 3.10+ from python.org and add it to PATH.
    echo.
    pause
    exit /b 1
)

echo Launching desktop application...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTICE] Application closed or exited with an error code.
    pause
)
