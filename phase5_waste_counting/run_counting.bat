@echo off
REM =========================================================================
REM  AI Smart Drainage - Waste Counting (Phase 5)
REM  Category-wise Waste Counting using YOLO tracking (persistent IDs)
REM  Easy run script for Windows
REM
REM  What this script does:
REM   1. Creates a virtual environment (venv) if it doesn't already exist.
REM   2. Activates the virtual environment.
REM   3. Installs required packages from requirements.txt.
REM   4. Runs main.py (opens webcam + tracking + category-wise counting).
REM =========================================================================

echo ==============================================================
echo  AI Smart Drainage - Waste Counting (Phase 5)
echo  Category-wise Counting (Plastic / Organic / Metal)
echo ==============================================================

REM Move to the folder where this batch file is located.
cd /d "%~dp0"

REM --- Step 1: Create virtual environment if missing ---
if not exist "venv\" (
    echo [INFO] Creating virtual environment "venv" ...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo         Make sure Python is installed and added to PATH.
        pause
        exit /b 1
    )
)

REM --- Step 2: Activate virtual environment ---
echo [INFO] Activating virtual environment ...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM --- Step 3: Install requirements ---
echo [INFO] Installing/checking required packages ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

REM --- Step 4: Run the main program ---
echo [INFO] Starting webcam waste tracking + counting ...
echo [INFO] Press R to reset counts. Press Q in the video window to quit.
python main.py

echo.
echo [INFO] Program finished. Press any key to close this window.
pause >nul
