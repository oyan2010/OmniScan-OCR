@echo off
title OmniScan OCR Studio
cd /d "%~dp0"
echo ==============================================
echo        Starting OmniScan OCR Studio...
echo ==============================================
python run.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] OmniScan exited with code %errorlevel%.
    pause
)
